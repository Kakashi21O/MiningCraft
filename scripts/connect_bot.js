/**
 * connect_bot.js  –  MiningCraft AFK Bot
 *
 * pyCraft only supports up to Minecraft 1.18.1 (protocol 757).
 * The Aternos server runs 1.21.4 (protocol 776), so we use mineflayer.
 *
 * Anti-AFK features:
 *   - Random jumps every 25-45 seconds
 *   - Slow look rotation (pans left/right) so the bot appears "alive"
 *   - Occasional sneak toggle
 *   - All intervals are randomised so the pattern is harder to detect
 *
 * Usage:
 *   node scripts/connect_bot.js
 *   npm run bot
 */

'use strict';

const mineflayer = require('mineflayer');
const fs         = require('fs');
const path       = require('path');
const yaml       = require('js-yaml');

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Random integer between min and max (inclusive). */
function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

/** Random float between min and max. */
function randFloat(min, max) {
  return Math.random() * (max - min) + min;
}

/** Schedule a callback after a random delay between minMs and maxMs. */
function randomTimeout(fn, minMs, maxMs) {
  return setTimeout(fn, randInt(minMs, maxMs));
}

// ─── Load config ─────────────────────────────────────────────────────────────

const configPath = path.resolve(__dirname, '../config/config.yaml');
let config;
try {
  config = yaml.load(fs.readFileSync(configPath, 'utf8'));
} catch (err) {
  console.error(`[ERROR] Could not read config: ${err.message}`);
  process.exit(1);
}

const HOST     = config.server.host;
const PORT     = config.server.port;
const USERNAME = config.bot.username;

// ─── Banner ──────────────────────────────────────────────────────────────────

console.log('\n=======================================================');
console.log(`  Starting MiningCraft AFK Bot: ${USERNAME}`);
console.log(`  Target Server: ${HOST}:${PORT}`);
console.log(`  Engine: mineflayer (supports 1.8 – 1.21+)`);
console.log(`  Anti-AFK: random jumps + look rotation + sneak`);
console.log('=======================================================\n');

// ─── Anti-AFK controller ─────────────────────────────────────────────────────

class AntiAfk {
  constructor(bot) {
    this.bot      = bot;
    this._timers  = [];
    this._yaw     = 0;        // current look direction (radians)
    this._lookDir = 1;        // 1 = turning right, -1 = turning left
    this._active  = false;
  }

  start() {
    if (this._active) return;
    this._active = true;
    console.log('[AFK] Anti-AFK started.');
    this._scheduleJump();
    this._scheduleSneak();
    this._startLookRotation();
  }

  stop() {
    this._active = false;
    this._timers.forEach(t => clearTimeout(t));
    this._timers = [];
    if (this._lookInterval) clearInterval(this._lookInterval);
    console.log('[AFK] Anti-AFK stopped.');
  }

  // ── Jump ────────────────────────────────────────────────────────────────────
  _scheduleJump() {
    if (!this._active) return;
    const delay = randInt(25000, 45000);   // jump every 25–45 s
    const t = setTimeout(() => {
      if (!this._active) return;
      this._doJump();
      this._scheduleJump();
    }, delay);
    this._timers.push(t);
  }

  _doJump() {
    const count = randInt(1, 3);           // 1–3 jumps in a row
    console.log(`[AFK] Jumping x${count}`);
    let i = 0;
    const jump = () => {
      if (!this._active || i >= count) return;
      this.bot.setControlState('jump', true);
      setTimeout(() => {
        this.bot.setControlState('jump', false);
        i++;
        if (i < count) setTimeout(jump, randInt(300, 600));
      }, 150);
    };
    jump();
  }

  // ── Sneak ────────────────────────────────────────────────────────────────────
  _scheduleSneak() {
    if (!this._active) return;
    const delay = randInt(40000, 70000);   // sneak every 40–70 s
    const t = setTimeout(() => {
      if (!this._active) return;
      this._doSneak();
      this._scheduleSneak();
    }, delay);
    this._timers.push(t);
  }

  _doSneak() {
    console.log('[AFK] Sneaking...');
    this.bot.setControlState('sneak', true);
    setTimeout(() => {
      this.bot.setControlState('sneak', false);
    }, randInt(800, 2000));
  }

  // ── Look rotation ────────────────────────────────────────────────────────────
  _startLookRotation() {
    // Slowly pan the bot's head left and right every 2 seconds
    this._lookInterval = setInterval(() => {
      if (!this._active) return;
      this._yaw += this._lookDir * randFloat(0.05, 0.15);   // small yaw step
      // Reverse direction every ~180°
      if (Math.abs(this._yaw) > Math.PI) this._lookDir *= -1;
      this.bot.look(this._yaw, 0, false).catch(() => {});
    }, 2000);
  }
}

// ─── Create bot ──────────────────────────────────────────────────────────────

function createBot() {
  console.log(`Connecting to ${HOST}:${PORT} as '${USERNAME}'...`);

  const bot = mineflayer.createBot({
    host:                 HOST,
    port:                 PORT,
    username:             USERNAME,
    auth:                 'offline',   // Aternos cracked / offline mode
    checkTimeoutInterval: 60000,
    keepAlive:            true,
  });

  const afk = new AntiAfk(bot);

  // ── Events ──────────────────────────────────────────────────────────────────

  bot.once('spawn', () => {
    const pos = bot.entity.position;
    console.log(`\n>>> [SUCCESS] ${USERNAME} connected and spawned into server!`);
    console.log(`    Position: x=${pos.x.toFixed(1)}, y=${pos.y.toFixed(1)}, z=${pos.z.toFixed(1)}`);
    console.log(`    Gamemode: ${bot.game.gameMode}`);
    console.log(`    World:    ${bot.game.dimension}`);
    console.log('\n>>> Bot is standing in the world. Press Ctrl+C to disconnect.\n');
    afk.start();
  });

  bot.on('message', (jsonMsg) => {
    const text = jsonMsg.toString();
    if (text.trim()) console.log(`[CHAT] ${text}`);
  });

  bot.on('error', (err) => {
    console.error(`\n[ERROR] ${err.message}`);
  });

  bot.on('kicked', (reason) => {
    afk.stop();
    console.log(`\n>>> [KICKED] Server kicked the bot: ${reason}`);
  });

  bot.on('end', (reason) => {
    afk.stop();
    console.log(`\n>>> [DISCONNECTED] Bot disconnected. Reason: ${reason}`);
    console.log('Bot shutdown complete.');
  });

  // ── Graceful shutdown ────────────────────────────────────────────────────────

  const shutdown = () => {
    console.log('\nStopping bot...');
    afk.stop();
    bot.quit('Disconnecting');
    setTimeout(() => process.exit(0), 500);
  };

  process.on('SIGINT',  shutdown);
  process.on('SIGTERM', shutdown);
}

createBot();
