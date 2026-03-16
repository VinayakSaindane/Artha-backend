const fs = require("fs");
const path = require("path");
const { validateSchemesDb } = require("./schemeSchema");

const SCHEMES_PATH = path.resolve(__dirname, "..", "data", "schemes.json");
const REFRESH_MS = 5 * 60 * 1000;

let cache = {
  db: null,
  mtimeMs: 0,
  checkedAt: 0,
};

function loadSchemesFromDisk() {
  const stats = fs.statSync(SCHEMES_PATH);
  const fileContent = fs.readFileSync(SCHEMES_PATH, "utf-8");
  const parsed = JSON.parse(fileContent);
  validateSchemesDb(parsed);

  cache.db = parsed;
  cache.mtimeMs = stats.mtimeMs;
  cache.checkedAt = Date.now();

  return parsed;
}

function getSchemesDb() {
  if (!cache.db) {
    return loadSchemesFromDisk();
  }

  const now = Date.now();
  if (now - cache.checkedAt < REFRESH_MS) {
    return cache.db;
  }

  cache.checkedAt = now;
  const stats = fs.statSync(SCHEMES_PATH);
  if (stats.mtimeMs > cache.mtimeMs) {
    return loadSchemesFromDisk();
  }

  return cache.db;
}

function getAllSchemes() {
  return getSchemesDb().schemes;
}

function getSchemesMeta() {
  const db = getSchemesDb();
  return {
    version: db.version,
    lastUpdated: db.lastUpdated,
  };
}

module.exports = {
  getSchemesDb,
  getAllSchemes,
  getSchemesMeta,
};
