-- The CRA index in Cloudflare D1. Each publication's text blocks are rows of `blocks`; `passages` is a
-- full-text index over them (external content, kept in step by the triggers), searched with bm25.
CREATE TABLE IF NOT EXISTS documents (
  id TEXT PRIMARY KEY,
  url TEXT UNIQUE NOT NULL,
  title TEXT,
  modified TEXT,
  retrieved TEXT,
  hash TEXT
);
CREATE TABLE IF NOT EXISTS blocks (
  id INTEGER PRIMARY KEY,
  doc_id TEXT NOT NULL,
  position INTEGER NOT NULL,
  title TEXT,
  text TEXT NOT NULL,
  UNIQUE (doc_id, position)
);
CREATE VIRTUAL TABLE IF NOT EXISTS passages USING fts5(title, text, content='blocks', content_rowid='id', tokenize='unicode61');
CREATE TRIGGER IF NOT EXISTS blocks_ai AFTER INSERT ON blocks BEGIN
  INSERT INTO passages(rowid, title, text) VALUES (new.id, new.title, new.text);
END;
CREATE TRIGGER IF NOT EXISTS blocks_ad AFTER DELETE ON blocks BEGIN
  INSERT INTO passages(passages, rowid, title, text) VALUES ('delete', old.id, old.title, old.text);
END;
