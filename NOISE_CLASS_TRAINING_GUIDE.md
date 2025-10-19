# 🎯 Noise Class Training Guide

## Problem Statement
Your ML models currently produce **false positives** when you make small, unintentional movements (fidgeting, adjusting your arm, etc.). This causes unwanted actions to trigger during gameplay.

## Solution: Add a "Noise" Class
Train both models to recognize and **ignore** random, non-intentional movements by adding a dedicated noise/rest class.

---

## 📊 Training Data Required

### **Binary Classifier (Locomotion)**
Currently: `["walk", "idle"]`
**New**: `["walk", "idle", "noise"]`

### **Multiclass Classifier (Actions)**
Currently: `["jump", "punch", "turn_left", "turn_right", "idle"]`
**New**: `["jump", "punch", "turn_left", "turn_right", "idle", "noise"]`

---

## 🎬 Data Collection Instructions

### **1. NOISE Class (For Both Models)**

**What to Capture:**
- Random arm movements (scratching, adjusting watch)
- Fidgeting, small hand gestures
- Picking up objects, drinking water
- Typing on keyboard with watch on
- Natural arm swinging while standing still
- Adjusting clothing or hair
- Quick wrist rotations
- Arm at rest but slight tremors/micro-movements

**Duration Per Sample:** 3-5 seconds
**Minimum Samples:** 30-40 samples
**Label in App:** `noise`

**How to Collect:**
1. Start recording in your data collection app
2. Make natural, random movements (don't think about it)
3. Do everyday activities while wearing the watch
4. Label as "noise" in the app
5. Repeat 30-40 times with variation

---

### **2. WALK Class (Binary Model)**

**What to Capture:**
- **Deliberate** walking motion with your arm
- Swing arm back and forth as if walking
- Can be done while sitting or standing
- Should be **distinct** and **intentional**

**Duration Per Sample:** 3-5 seconds
**Minimum Samples:** You already have this! Review existing data.
**Label in App:** `walk`

**Key Distinction from Noise:**
- Walk = **deliberate, rhythmic** arm swing
- Noise = **random, non-rhythmic** movements

---

### **3. IDLE Class (Both Models)**

**What to Capture:**
- Arm completely still
- Watch on wrist, no movement
- Relaxed position (arm at side, on desk, etc.)
- Controlled stillness (not fidgeting)

**Duration Per Sample:** 3-5 seconds
**Minimum Samples:** You already have this! Review existing data.
**Label in App:** `idle`

**Key Distinction from Noise:**
- Idle = **intentionally still** (no movement)
- Noise = **unintentional small movements**

---

### **4. Action Classes (Multiclass Model)**

#### **JUMP**
- Quick upward arm thrust
- Sharp, sudden upward motion
- Like jumping in a platformer game

**Duration:** 1-2 seconds
**Samples Needed:** 20-30
**Distinction:** **Fast vertical** motion vs noise (random)

---

#### **PUNCH**
- Forward thrusting motion
- Quick jab or punch gesture
- Like attacking in a game

**Duration:** 1-2 seconds
**Samples Needed:** 20-30
**Distinction:** **Fast horizontal/forward** motion vs noise (random)

---

#### **TURN_LEFT**
- Rotate wrist/arm to the left
- Smooth turning motion
- Like steering or looking left

**Duration:** 1-2 seconds
**Samples Needed:** 20-30
**Distinction:** **Deliberate rotation** vs noise (random wrist movement)

---

#### **TURN_RIGHT**
- Rotate wrist/arm to the right
- Smooth turning motion
- Like steering or looking right

**Duration:** 1-2 seconds
**Samples Needed:** 20-30
**Distinction:** **Deliberate rotation** vs noise (random wrist movement)

---

## 📋 Data Collection Checklist

### Binary Classifier Data
- [ ] 30-40 **noise** samples (NEW!)
- [ ] Review existing **walk** samples (should have ~30+)
- [ ] Review existing **idle** samples (should have ~30+)

### Multiclass Classifier Data
- [ ] 30-40 **noise** samples (NEW!)
- [ ] Review existing **jump** samples
- [ ] Review existing **punch** samples
- [ ] Review existing **turn_left** samples
- [ ] Review existing **turn_right** samples
- [ ] Review existing **idle** samples

---

## 🔄 Retraining Workflow

After collecting noise data:

1. **Merge new noise data** with existing datasets
   ```bash
   python src/merge_sensor_rows.py
   ```

2. **Organize training data** (will now include noise class)
   ```bash
   python src/organize_training_data.py
   ```

3. **Retrain models** with updated classes
   ```bash
   python notebooks/SVM_Local_Training.py
   ```

4. **Update code** to handle noise predictions:
   - Modify `BINARY_CLASSES` to `["walk", "idle", "noise"]`
   - Modify `MULTI_CLASSES` to `["jump", "punch", "turn_left", "turn_right", "idle", "noise"]`
   - Filter out "noise" predictions in the actor (treat same as "idle")

---

## 🎯 Expected Results

### Before Adding Noise Class:
- Random movements → Trigger false actions ❌
- Small fidgets → Character moves ❌
- Adjusting watch → Game responds ❌

### After Adding Noise Class:
- Random movements → Ignored ✅
- Small fidgets → No action ✅
- Adjusting watch → No response ✅
- **Only deliberate gestures trigger actions** ✅

---

## 💡 Pro Tips

1. **Vary your noise samples**: Different types of random movements
2. **Make actions exaggerated**: Clear distinction from noise
3. **Collect in realistic conditions**: Same environment as gameplay
4. **Balance your dataset**: ~Equal samples per class
5. **Test incrementally**: Add noise class, retrain, test, iterate

---

## 🚀 Next Steps

1. **Collect 30-40 noise samples** for both models
2. **Review existing samples** to ensure quality
3. **Retrain models** with new 3-class (binary) and 6-class (multi) setup
4. **Update dashboard code** to filter noise predictions
5. **Test in gameplay** - should feel much more responsive and accurate!

---

## 📞 Questions?

- Not sure if a movement is "noise" or an action? → If you **didn't intend it**, it's noise!
- How exaggerated should actions be? → Clear enough that you can tell the difference yourself
- Can I combine idle and noise? → No! Idle = still, Noise = small movements

Good luck! 🎮
