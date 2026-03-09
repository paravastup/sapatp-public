# Finding Windows Host IP for WSL2 Docker Access

## The Problem
- Ollama runs on **Windows**
- Docker runs inside **WSL2**
- Docker containers need to access Windows Ollama

## Solution: Find Windows IP Accessible from WSL2

### Step 1: Find Windows IP from PowerShell/CMD

Open PowerShell or CMD on Windows and run:

```powershell
ipconfig
```

Look for the **"vEthernet (WSL)"** adapter - this is the IP that WSL2 uses to talk to Windows.

It will look something like:
```
Ethernet adapter vEthernet (WSL):
   IPv4 Address. . . . . . . . . . . : 192.168.1.100
```

**That IP (e.g., 192.168.1.100) is what you need!**

### Step 2: Verify Ollama is Accessible from WSL2

From WSL2 terminal, test with that IP:

```bash
# Replace 192.168.1.100 with YOUR vEthernet (WSL) IP
curl http://192.168.1.100:11434/api/tags
```

If this works, you'll see your Ollama models listed!

### Step 3: Update Docker Configuration

Once you have the correct IP, I'll update the docker-compose file with it.

---

## Alternative: Check from WSL2

From WSL2, you can also try:

```bash
# This often shows the Windows host IP
cat /etc/resolv.conf | grep nameserver | grep -v 8.8.8.8 | grep -v 1.1.1.1

# Or get it from routing table
ip route | grep default | awk '{print $3}'
```

But the vEthernet (WSL) IP from Windows ipconfig is the most reliable!

---

## Important Note

If Ollama on Windows is only listening on localhost (127.0.0.1), you may need to:

### Make Ollama Listen on All Interfaces

**Option 1: Set environment variable in Windows**
1. Open System Properties → Environment Variables
2. Add: `OLLAMA_HOST=0.0.0.0:11434`
3. Restart Ollama

**Option 2: Start Ollama with --host flag** (if supported)

**Option 3: Edit Ollama service configuration** (depends on how you installed it)

---

## Quick Test Workflow

1. Find Windows vEthernet (WSL) IP with `ipconfig` → Note the IP
2. Test from WSL2: `curl http://YOUR_VETHERNET_IP:11434/api/tags`
3. If it works: Update docker-compose-port5000-secure.yml with that IP
4. If it doesn't work: Configure Ollama to listen on 0.0.0.0
5. Restart Docker containers

---

Let me know the IP address and I'll update everything for you!