# Watch Connection Troubleshooting

## 🔍 Current Status

✅ **Python Controller**: Running on `192.168.10.130:12345`
✅ **UDP Socket**: Bound and listening
❌ **Android App**: Not connected yet

## 📱 Android App Connection Steps

### 1. **Open Your Android App**
   - The app that sends sensor data (from Android_2_Grid or Android folder)
   - Should have an IP address input field

### 2. **Enter Mac IP Address**
   ```
   192.168.10.130
   ```
   - **Port is hardcoded**: 12345
   - Make sure NO extra spaces
   - Should match exactly what you see in controller output

### 3. **Ensure Same WiFi Network**
   ```bash
   # Mac network:
   192.168.10.130/24 (subnet: 192.168.10.0)

   # Android should be on same subnet:
   192.168.10.xxx (where xxx is different from 130)
   ```

### 4. **Check Android App is Sending Data**
   - Look for "Start" or "Connect" button in app
   - App should show "Connected" or "Sending data"
   - Should see Hz counter or packet rate

## 🐛 Common Issues

### Issue 1: Android App Not Installed
**Solution**: Build and install the Android app first

```bash
# From Android_2_Grid or Android folder:
cd Android_2_Grid
./gradlew assembleDebug

# Install APK to phone:
adb install app/build/outputs/apk/debug/app-debug.apk
```

### Issue 2: Wrong IP Address in App
**Current Mac IP**: `192.168.10.130`

- ❌ Wrong: `172.29.85.16` (old IP)
- ❌ Wrong: `0.0.0.0` (listen all, not for Android)
- ✅ Correct: `192.168.10.130`

### Issue 3: Firewall Blocking UDP
```bash
# Check if macOS firewall is blocking:
# System Settings > Network > Firewall > Options
# Allow incoming connections for Python

# Or temporarily disable firewall for testing:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate off
```

### Issue 4: Different WiFi Networks
**Mac and Android MUST be on same network**

```bash
# Check Mac network:
ifconfig | grep "inet " | grep -v 127.0.0.1
# Should show: inet 192.168.10.130

# Check Android network:
# Settings > WiFi > Connected Network > IP Address
# Should show: 192.168.10.xxx (same subnet)
```

### Issue 5: Android App Permissions
Android app needs:
- ✅ **INTERNET** permission
- ✅ **BODY_SENSORS** permission (for accelerometer/gyro)
- ✅ **WAKE_LOCK** permission (to prevent sleep)

Check in `AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.BODY_SENSORS" />
```

## 🧪 Testing Connection

### Test 1: Manual UDP Packet (from another terminal)
```bash
# Send test packet to verify listener is working:
echo "SENSOR:1.0,2.0,3.0,0.1,0.2,0.3" | nc -u 192.168.10.130 12345
```

**Expected**: Controller should show `[✓ CONNECTED]` briefly

### Test 2: Python Test Script
```bash
# Create test_udp.py:
cat > test_udp.py << 'EOF'
import socket
import time

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
for i in range(100):
    msg = f"SENSOR:1.0,2.0,3.{i},0.1,0.2,0.3"
    sock.sendto(msg.encode(), ("192.168.10.130", 12345))
    time.sleep(0.033)  # ~30Hz
    print(f"Sent packet {i}")
EOF

# Run test:
python test_udp.py
```

**Expected**: Controller should show:
```
[✓ CONNECTED] [30 Hz] | Walk: 🧍 IDLE (→) | ...
```

### Test 3: Check for UDP Traffic
```bash
# In another terminal:
sudo tcpdump -i any -n udp port 12345

# Should see packets if Android is sending:
# IP 192.168.10.xxx.12345 > 192.168.10.130.12345: UDP...
```

## 📱 Which Android App?

You have TWO Android folders in the workspace:

### Option 1: `Android/` (original)
```bash
cd /Users/cvk/Downloads/CODELocalProjects/v3pls/Android
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

### Option 2: `Android_2_Grid/` (newer?)
```bash
cd /Users/cvk/Downloads/CODELocalProjects/v3pls/Android_2_Grid
./gradlew assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

**Check which one has sensor streaming code:**
```bash
# Search for UDP sending code:
grep -r "DatagramSocket\|DatagramPacket" Android*/app/src/
grep -r "SENSOR:" Android*/app/src/
```

## ✅ What Should Happen When Connected

1. **Controller terminal shows**:
   ```
   [✓ CONNECTED] [30 Hz] | Walk: 🧍 IDLE (→) | Action: - (0%) | State: Idle
   ```

2. **Android app shows**:
   - "Connected" status
   - Sensor data streaming
   - Packet count increasing

3. **When you move phone**:
   ```
   [✓ CONNECTED] [30 Hz] | Walk: 🚶 WALKING (→) | Action: idle (65%) | State: Walking
   ```

## 🔧 Quick Fix Checklist

- [ ] Android app installed on phone
- [ ] Same WiFi network (both 192.168.10.xxx)
- [ ] Correct IP in Android app: `192.168.10.130`
- [ ] Port is 12345 (usually hardcoded)
- [ ] Android app "Start" button pressed
- [ ] Phone sensors working (test in other apps)
- [ ] macOS firewall allows Python
- [ ] No other process using port 12345

## 🚀 Next Steps

1. **Install Android App**
   ```bash
   cd Android_2_Grid  # or Android
   ./gradlew assembleDebug
   adb install app/build/outputs/apk/debug/app-debug.apk
   ```

2. **Open App on Phone**
   - Enter IP: `192.168.10.130`
   - Tap "Start" or "Connect"

3. **Move Phone**
   - Should see data rate increase: `[30 Hz]`
   - Should see `[✓ CONNECTED]`

4. **Start Walking!**
   - Hold phone horizontal
   - Swing arm naturally
   - Should see: `Walk: 🚶 WALKING (→)`

---

**Current Status**: Controller is ready and waiting for Android app to connect! 📱➡️💻
