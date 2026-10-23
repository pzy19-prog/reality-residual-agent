// JSON-lines bridge: RRA (Python) <-> Meterless H-MEM reference implementation.
// One request per stdin line, one response per stdout line. Nothing else may
// write to stdout. The HMEM clock is a deterministic counter, never Date.now.

import readline from "node:readline";
import { HMEM } from "./vendor/Meterless/engines/hmem/reference/src/index.ts";

const SOURCE = "rra.s2";
const KINDS = new Set(["run", "manifest"]);

type Req = Record<string, unknown>;

class BridgeError extends Error {
  constructor(readonly code: string, message: string) {
    super(message);
  }
}

let hmem: HMEM | undefined;
let actor = "rra-bridge";
let runTag: string | undefined;

function str(req: Req, key: string): string {
  const v = req[key];
  if (typeof v !== "string" || v === "") throw new BridgeError("E_BAD_REQUEST", `${key} must be a non-empty string`);
  return v;
}

function opened(): HMEM {
  if (!hmem) throw new BridgeError("E_BAD_REQUEST", "store not opened");
  return hmem;
}

function tagValue(tags: string[], prefix: string): string | undefined {
  return tags.find((t) => t.startsWith(prefix))?.slice(prefix.length);
}

function handle(req: Req): Record<string, unknown> {
  switch (req.op) {
    case "open": {
      if (hmem) throw new BridgeError("E_BAD_REQUEST", "store already opened");
      const storeDir = str(req, "store_dir");
      const start = req.clock_start_ms;
      if (typeof start !== "number" || !Number.isInteger(start) || start < 0) {
        throw new BridgeError("E_BAD_REQUEST", "clock_start_ms must be a non-negative integer");
      }
      if (req.actor !== undefined) actor = str(req, "actor");
      if (req.run_tag !== undefined) runTag = str(req, "run_tag");
      let tick = start;
      hmem = new HMEM({ clock: () => tick++, persistDir: storeDir, actor });
      return { store_dir: storeDir, records: hmem.store.all().length };
    }
    case "put": {
      const h = opened();
      const episodeId = str(req, "episode_id");
      const kind = str(req, "kind");
      const content = str(req, "content");
      if (!KINDS.has(kind)) throw new BridgeError("E_BAD_REQUEST", `kind must be one of ${[...KINDS].join(", ")}`);
      const rec = h.add({
        content,
        source: SOURCE,
        chatId: episodeId,
        missionId: runTag,
        tags: ["rra", "s2", `episode:${episodeId}`, `kind:${kind}`],
      });
      return { memory_id: rec.id, timestamp: rec.timestamp };
    }
    case "get": {
      const h = opened();
      const reader = str(req, "reader_episode_id");
      const id = str(req, "memory_id");
      const rec = h.store.get(id);
      if (!rec) throw new BridgeError("E_NOT_FOUND", `unknown memory id ${id}`);
      if (rec.chatId !== reader) {
        // Refused before any ledger write: a cross-episode attempt leaves no read entry.
        throw new BridgeError("E_CROSS_EPISODE", `memory ${id} belongs to another episode`);
      }
      h.ledger.log(id, "read", actor, { details: { reader_episode_id: reader, record_episode_id: rec.chatId } });
      return {
        memory_id: rec.id,
        episode_id: rec.chatId,
        kind: tagValue(rec.tags, "kind:") ?? null,
        timestamp: rec.timestamp,
        content: rec.content,
      };
    }
    case "list": {
      const h = opened();
      const reader = str(req, "reader_episode_id");
      const items = h.store
        .all()
        .filter((r) => r.chatId === reader)
        .sort((a, b) => Number(a.id.slice(4)) - Number(b.id.slice(4)))
        .map((r) => ({ memory_id: r.id, kind: tagValue(r.tags, "kind:") ?? null, timestamp: r.timestamp }));
      return { items };
    }
    case "close":
      return { closed: true };
    default:
      throw new BridgeError("E_BAD_REQUEST", `unknown op ${JSON.stringify(req.op)}`);
  }
}

function respond(body: Record<string, unknown>, then?: () => void): void {
  process.stdout.write(JSON.stringify(body) + "\n", then);
}

const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
for await (const line of rl) {
  if (line.trim() === "") continue;
  let req: Req;
  try {
    const parsed: unknown = JSON.parse(line);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) throw new Error("not an object");
    req = parsed as Req;
  } catch {
    respond({ ok: false, code: "E_BAD_REQUEST", message: "request is not a JSON object" });
    continue;
  }
  try {
    const out = handle(req);
    respond({ ok: true, ...out }, req.op === "close" ? () => process.exit(0) : undefined);
    if (req.op === "close") break;
  } catch (e) {
    if (e instanceof BridgeError) respond({ ok: false, code: e.code, message: e.message });
    else respond({ ok: false, code: "E_INTERNAL", message: String((e as Error)?.message ?? e) });
  }
}
