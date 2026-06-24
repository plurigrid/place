import sqlite3 from 'sqlite3';
import * as Y from 'yjs';
import { Extension, onLoadDocumentPayload, onChangePayload } from '@hocuspocus/server';
export declare const schema = "CREATE TABLE IF NOT EXISTS \"documents\" (\n  \"name\" varchar(255) NOT NULL,\n  \"data\" blob NOT NULL,\n  UNIQUE(name)\n)";
export declare const selectQuery = "\n  SELECT data FROM \"documents\" where name = $name ORDER BY rowid DESC\n";
export declare const upsertQuery = "\n  INSERT INTO \"documents\" (\"name\", \"data\") VALUES ($name, $data)\n    ON CONFLICT(name) DO UPDATE SET data = $data\n";
export interface SQLiteWithFSConfiguration {
    databasePath: string;
    contentRoot: string;
    schema: string;
}
export declare class SQLiteWithFS implements Extension {
    db: sqlite3.Database;
    contentRoot: string;
    constructor(db: sqlite3.Database, contentRoot: string);
    onLoadDocument(data: onLoadDocumentPayload): Promise<Y.Doc>;
    getPath(name: string): string;
    onStoreDocument(data: onChangePayload): Promise<void>;
}
