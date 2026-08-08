/// ScanView.swift — RoomPlan capture session + ARKit point cloud extraction
///
/// This is the iOS-only scanning UI. It runs RoomPlan's RoomCaptureView
/// which provides real-time room understanding with LiDAR, then exports:
///   1. CapturedRoom → USDZ (structured room model)
///   2. ARFrame.sceneDepth → PLY point cloud
///   3. Placement analysis → JSON zones for chair/screen/pegboard
///
/// Build: open in Xcode, run on LiDAR device, scan the BCI station space.

#if canImport(RoomPlan) && canImport(ARKit)

import SwiftUI
import RoomPlan
import ARKit

// MARK: - Room Capture Coordinator

@available(iOS 17.0, *)
class BCIRoomCaptureDelegate: NSObject, RoomCaptureViewDelegate, RoomCaptureSessionDelegate {
    var capturedRoom: CapturedRoom?
    var pointCloud = PointCloud()
    var onComplete: ((CapturedRoom, PointCloud) -> Void)?

    func captureView(shouldPresent roomDataForProcessing: CapturedRoomData, error: (Error)?) -> Bool {
        return true
    }

    func captureView(didPresent processedResult: CapturedRoom, error: (Error)?) {
        self.capturedRoom = processedResult
        analyzePlacement(room: processedResult)
    }

    func captureSession(_ session: RoomCaptureSession, didUpdate room: CapturedRoom) {
        // Real-time updates during scanning — could feed live to ghostty-ix
    }

    func captureSession(_ session: RoomCaptureSession, didProvide instruction: RoomCaptureSession.Instruction) {
        // Coaching: "Move closer to wall", "Scan floor", etc.
    }

    func captureSession(_ session: RoomCaptureSession, didEndWith data: CapturedRoomData, error: (Error)?) {
        // Scan complete
    }

    // MARK: - Placement Analysis

    func analyzePlacement(room: CapturedRoom) {
        var zones: [PlacementZone] = []

        // Find walls suitable for screen and pegboard
        for wall in room.walls {
            let transform = wall.transform
            let dims = wall.dimensions // simd_float3
            let center = simd_float3(transform.columns.3.x,
                                      transform.columns.3.y,
                                      transform.columns.3.z)

            // Screen zone: wall segment at eye height (1.1-1.4m)
            if dims.x >= 0.5 {
                let screenCenter = [center.x, center.y, Float(1.25)]
                let nearWindow = room.windows.contains { w in
                    let wPos = simd_float3(w.transform.columns.3.x,
                                           w.transform.columns.3.y,
                                           w.transform.columns.3.z)
                    return simd_distance(simd_float2(center.x, center.y),
                                        simd_float2(wPos.x, wPos.y)) < 1.0
                }

                zones.append(PlacementZone(
                    trit: .horse,
                    center: screenCenter,
                    normal: [transform.columns.2.x, transform.columns.2.y, transform.columns.2.z],
                    dimensions: [0.6, 0.4, 0.05],
                    score: PlacementZone.scoreForScreen(
                        wallWidth: dims.x,
                        height: 1.25,
                        hasWindow: nearWindow
                    ),
                    reason: "Wall \(dims.x)m wide, \(nearWindow ? "has" : "no") window nearby"
                ))

                // Pegboard: adjacent to screen, same wall
                if dims.x >= 1.0 {
                    zones.append(PlacementZone(
                        trit: .red,
                        center: [center.x + 0.5, center.y, Float(1.0)],
                        normal: [transform.columns.2.x, transform.columns.2.y, transform.columns.2.z],
                        dimensions: [0.4, 0.6, 0.1],
                        score: PlacementZone.scoreForPegboard(wallWidth: dims.x - 0.6, distToChair: 0.7),
                        reason: "Right of screen candidate, same wall"
                    ))
                }
            }
        }

        // Chair zone: floor area in front of best screen candidate
        if let bestScreen = zones.filter({ $0.trit == .horse }).max(by: { $0.score < $1.score }) {
            let normal = bestScreen.normal
            let chairCenter = [
                bestScreen.center[0] - normal[0] * 0.8,
                bestScreen.center[1] - normal[1] * 0.8,
                Float(0.0)
            ]

            // Check door clearance
            let minDoorDist = room.doors.map { door -> Float in
                let dPos = simd_float3(door.transform.columns.3.x,
                                       door.transform.columns.3.y,
                                       door.transform.columns.3.z)
                return simd_distance(simd_float2(chairCenter[0], chairCenter[1]),
                                     simd_float2(dPos.x, dPos.y))
            }.min() ?? 99.0

            zones.append(PlacementZone(
                trit: .blue,
                center: chairCenter,
                normal: [0, 0, 1],
                dimensions: [0.7, 0.5, 0.7],
                score: PlacementZone.scoreForChair(floorArea: 0.49, distToWall: 0.8, distToDoor: minDoorDist),
                reason: "Floor in front of best screen, \(minDoorDist)m from door"
            ))
        }

        print("Found \(zones.count) placement zones")
        for z in zones {
            print("  \(z.trit.label) (\(z.trit.rawValue)): score \(z.score) — \(z.reason)")
        }
    }
}

// MARK: - SwiftUI Scan View

@available(iOS 17.0, *)
struct BCIScanView: View {
    @State private var isScanning = false

    var body: some View {
        VStack {
            Text("BCI Station Scanner")
                .font(.headline)
            Text("−1 chair · 0 screen · +1 pegboard")
                .font(.caption)
                .foregroundColor(.secondary)

            RoomCaptureViewRepresentable()
                .edgesIgnoringSafeArea(.all)
        }
    }
}

@available(iOS 17.0, *)
struct RoomCaptureViewRepresentable: UIViewRepresentable {
    func makeUIView(context: Context) -> RoomCaptureView {
        let view = RoomCaptureView(frame: .zero)
        let delegate = BCIRoomCaptureDelegate()
        view.delegate = delegate
        view.captureSession.run(configuration: .init())
        return view
    }

    func updateUIView(_ uiView: RoomCaptureView, context: Context) {}
}

#endif

// MARK: - Point Cloud from ARKit Depth (works alongside RoomPlan)

#if os(iOS) && canImport(ARKit)

import ARKit

@available(iOS 14.0, *)
extension PointCloud {
    /// Extract point cloud from ARFrame's scene depth
    /// LiDAR provides depth at ~256×192 resolution, ~30Hz
    mutating func ingestARFrame(_ frame: ARFrame) {
        guard let depthMap = frame.sceneDepth?.depthMap else { return }

        let width = CVPixelBufferGetWidth(depthMap)
        let height = CVPixelBufferGetHeight(depthMap)
        let intrinsics = frame.camera.intrinsics
        let viewMatrix = frame.camera.viewMatrix(for: .landscapeRight)

        CVPixelBufferLockBaseAddress(depthMap, .readOnly)
        defer { CVPixelBufferUnlockBaseAddress(depthMap, .readOnly) }

        guard let baseAddress = CVPixelBufferGetBaseAddress(depthMap) else { return }
        let floatBuffer = baseAddress.assumingMemoryBound(to: Float32.self)

        // Subsample: every 4th pixel to keep cloud manageable
        let stride = 4
        for y in Swift.stride(from: 0, to: height, by: stride) {
            for x in Swift.stride(from: 0, to: width, by: stride) {
                let depth = floatBuffer[y * width + x]
                guard depth > 0 && depth < 5.0 else { continue } // 0-5m range

                // Unproject pixel to 3D using camera intrinsics
                let fx = intrinsics[0][0]
                let fy = intrinsics[1][1]
                let cx = intrinsics[2][0]
                let cy = intrinsics[2][1]

                let localX = (Float(x) - cx) * depth / fx
                let localY = (Float(y) - cy) * depth / fy
                let localZ = depth

                // Transform to world coordinates
                let local = simd_float4(localX, localY, localZ, 1.0)
                let world = viewMatrix.inverse * local

                points.append(Point3D(
                    x: world.x,
                    y: world.y,
                    z: world.z,
                    r: 128, g: 128, b: 128, // gray until classified
                    classification: classifyByHeight(z: world.z)
                ))
            }
        }
    }

    /// Simple height-based classification
    func classifyByHeight(z: Float) -> Point3D.Classification {
        if z < 0.05 { return .floor }
        if z > 2.5 { return .ceiling }
        return .wall // refined by RoomPlan structured output
    }
}

#endif
