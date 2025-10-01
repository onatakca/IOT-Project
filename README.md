Ideas:

## 1. Core Concept

* **Input**: Two Thingy:52 devices act as **paddles** (one in each hand).
* **Controls**:

  * **Both paddles moved (in synch)** = go straight.
  * **Only left moved** = turn right.
  * **Only right moved** = turn left.
  * **No movement (or moving randomly)** = stop.
* **Output**: A simple canoe game running on Raspberry Pi (or laptop), displayed on a screen, with obstacles scrolling down to avoid.

---

## 2. System Architecture

**Thingy:52 (left + right)**

* On-board IMU (accelerometer/gyroscope) detects paddling movement.
* Tiny ML model (or threshold logic) classifies “paddle” vs “no paddle.”
* Sends classification result via **Bluetooth**.

**Raspberry Pi (Game Engine + Gateway)**

* Receives BLE data from both paddles.
* Decides canoe movement (straight / left / right / stop).
* Updates canoe position in the game.

**Game (UI)**

* Simple 2D game (e.g., built in Python with **Pygame**) showing:

  * Canoe at bottom of screen.
  * Obstacles coming from top (random positions).
  * Collision detection + score counter.

---

## 3. ML & Detection Logic

### Option A (simplest, no heavy ML):

* Detect paddle strokes with **acceleration threshold** on the Y-axis (back and forth movement).
* If accel_y crosses threshold → paddle detected.
* Works fine for a game demo.

### Option B (with ML on Thingy, for higher grade):

* Train small classifier on IMU windows (1 sec). Classes: `{paddle, idle}`.
* Model: Tiny 1D CNN or fully connected network (int8 quantized).
* Deploy to Thingy:52 using **TensorFlow Lite Micro**.

Both options satisfy “partly ML on-device,” but Option B looks better for the presentation.

---

## 4. Connectivity

* Use **BLE GATT services** to send state.
* Each Thingy sends one byte every ~100 ms:

  * `0 = idle`, `1 = paddle detected`.
* Raspberry Pi connects to both Thingies and combines signals to decide direction.

---

## 5. Game Logic

* Game loop runs at ~30 FPS.
* Movement rules:

  * Both paddles = move up (straight).
  * Left only = move up + slightly right.
  * Right only = move up + slightly left.
  * None = stop (canoe drifts down slowly).
* Obstacles:

  * Spawn randomly at top, move downward.
  * Collision → game over.
* Scoring: survive time or obstacles passed.

---

## 6. Scalability

* Works with any number of players (two paddles per canoe).
* BLE connection accepts multiple Thingies → game can handle more canoes in multiplayer.
* Shows “generalizable to unseen devices.”

---

## 7. User Interface (Demo)

* Set the left and right thingy in the beginning 
* Show the canoe moving on a projected screen.
* Two students paddle in front of the class with Thingies.
* Everyone sees the canoe dodge obstacles live.
* Add fun effects: splash sound when paddling, score counter, high score table.

---

## 8. Group Task Split

* **Firmware team (2 ppl)**: IMU paddle detection (threshold or ML), BLE service.
* **Connectivity team (1 ppl)**: Raspberry Pi BLE client, data parsing.
* **Game team (2 ppl)**: Pygame development (canoe, obstacles, collision, scoring).

---

## 9. Demo Flow (5 minutes)

1. Show Thingy as paddle → shake = paddle detection (LED blink as feedback).
2. Open game on screen → canoe at bottom.
3. One person paddle → canoe moves straight, left, right.
4. Obstacles appear → try to survive!
5. Score displayed, collision ends game.

---

## 10. Stretch Ideas (optional, if time allows)

* **ML gestures**: Different paddle styles = different speeds.
* **Obstacles with themes** (rocks, logs, whirlpools).
* **Multiplayer**: 2 canoes on screen, race mode.
* **Cloud logging**: Upload game scores to a leaderboard.

---

⚡ In short:

* Detect paddle strokes with IMU.
* Send paddle/no-paddle over BLE.
* Pi fuses signals into canoe movement.
* Pygame runs the canoe game with obstacles + scoring.
* Demo = live paddling in class.


