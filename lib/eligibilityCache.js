const TTL_MS = 24 * 60 * 60 * 1000;
const MAX_ITEMS = 500;

const cache = new Map();

function key(userId, category, profileVersion) {
  return `${userId || "anonymous"}:${category || "all"}:${profileVersion || 0}`;
}

function get(userId, category, profileVersion) {
  const cacheKey = key(userId, category, profileVersion);
  const entry = cache.get(cacheKey);
  if (!entry) return null;

  const expired = Date.now() - entry.timestamp > TTL_MS;
  if (expired) {
    cache.delete(cacheKey);
    return null;
  }

  return {
    ...entry.value,
    lastCheckedAt: entry.timestamp,
    fromCache: true,
  };
}

function set(userId, category, profileVersion, value) {
  const cacheKey = key(userId, category, profileVersion);
  if (cache.size >= MAX_ITEMS) {
    const oldestKey = cache.keys().next().value;
    if (oldestKey) cache.delete(oldestKey);
  }

  cache.set(cacheKey, {
    timestamp: Date.now(),
    value,
  });
}

function invalidateUser(userId) {
  const prefix = `${userId || "anonymous"}:`;
  for (const cacheKey of cache.keys()) {
    if (cacheKey.startsWith(prefix)) {
      cache.delete(cacheKey);
    }
  }
}

module.exports = {
  get,
  set,
  invalidateUser,
};
