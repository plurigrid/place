import { Hocuspocus } from '@hocuspocus/server';
import { RedisClientType } from 'redis';
import sqlite3 from 'sqlite3';
export declare function startBuilder(hocuspocus: Hocuspocus, _db: sqlite3.Database, subscriber: RedisClientType, writer: RedisClientType, forestDir: string, contentRoot: string): Promise<void>;
