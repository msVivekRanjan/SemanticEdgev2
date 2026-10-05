# SemanticEdge --- Remote Sparsh CCTV RTSP Access via Tailscale

This README documents the **exact networking setup used for the
SemanticEdge project** to access a Sparsh IP CCTV camera located in the
university's 5G Use Case Lab from a MacBook at a remote location (for
example, New Delhi).

This is **not a generic Tailscale guide**. The IP addresses, machines,
commands, and network topology below correspond to the SemanticEdge
setup.

------------------------------------------------------------------------

## 1. Objective

The goal was to keep the Sparsh CCTV camera inside the university's
Signaltron-supported 5G network while allowing the SemanticEdge laptop
at a remote location to consume the camera's **original RTSP stream
directly**.

The final flow is:

``` text
Sparsh IP CCTV
      |
      | RTSP
      v
University 5G Network
      |
      v
ue1 (Linux)
192.168.128.127
      |
      | Tailscale subnet routing
      |
      v
Internet
      |
      v
SemanticEdge MacBook
100.118.232.36 (Tailscale IP)
      |
      | RTSP
      v
SemanticEdge
      |
      v
YOLO / AI Processing
```

The camera itself does **not** run Tailscale.

The Linux machine `ue1` acts as the **Tailscale subnet router**.

------------------------------------------------------------------------

## 2. Hardware / Machines Used

### Camera

-   Device: **Sparsh IP CCTV camera**
-   Camera IP: **`192.168.128.10`**
-   RTSP port: **`554`**
-   Network: University Signaltron 5G Use Case Lab network

The camera was already known to provide a working RTSP stream locally.

> **Important:** The actual RTSP username, password, and stream path are
> intentionally not stored in this README. Do not commit camera
> credentials to Git.

------------------------------------------------------------------------

### University-side Linux machine

-   Hostname: **`ue1`**
-   OS: Linux
-   LAN IP: **`192.168.128.127`**
-   Network interface connected to the camera network: **`eno1`**
-   Tailscale IP: **`100.124.178.101`**

This machine is the **subnet router**.

It can directly access the camera because both are on:

``` text
192.168.128.0/24
```

------------------------------------------------------------------------

### Remote SemanticEdge MacBook

-   Device: MacBook
-   Tailscale hostname: **`viveks-macbook-air`**
-   Tailscale IP: **`100.118.232.36`**

This is the machine running SemanticEdge and YOLO during the remote
demonstration.

------------------------------------------------------------------------

## 3. Network Information

The important network values for this setup are:

  Component             Address
  --------------------- --------------------
  Sparsh CCTV           `192.168.128.10`
  `ue1` LAN IP          `192.168.128.127`
  `ue1` LAN interface   `eno1`
  Camera network        `192.168.128.0/24`
  Camera RTSP port      `554`
  `ue1` Tailscale IP    `100.124.178.101`
  Mac Tailscale IP      `100.118.232.36`

The route from `ue1` to the camera was verified using:

``` bash
ip route get 192.168.128.10
```

Output:

``` text
192.168.128.10 dev eno1 src 192.168.128.127 uid 1000
     cache
```

This confirmed:

``` text
Camera:     192.168.128.10
ue1 source: 192.168.128.127
Interface:  eno1
```

Therefore the camera subnet to advertise through Tailscale is:

``` text
192.168.128.0/24
```

------------------------------------------------------------------------

# 4. Why Tailscale Subnet Routing Was Used

The camera cannot be treated like a normal Internet-facing device.

Its address:

``` text
192.168.128.10
```

is a private IP address.

The remote Mac cannot normally reach it directly over the Internet.

Instead, `ue1` acts as a gateway:

``` text
Remote Mac
    |
    | Tailscale
    v
   ue1
    |
    | Local LAN
    v
192.168.128.10
    |
    v
Sparsh CCTV
```

This is called **subnet routing**.

The camera does not need Tailscale installed.

------------------------------------------------------------------------

# 5. Tailscale Setup

Both machines were first added to the same Tailscale tailnet.

The resulting machines were:

``` text
ue1
100.124.178.101

viveks-macbook-air
100.118.232.36
```

Verify the machines using:

``` bash
tailscale status
```

Expected relevant entries:

``` text
100.124.178.101    ue1
100.118.232.36     viveks-macbook-air
```

------------------------------------------------------------------------

# 6. Verify Camera Connectivity Before Tailscale Routing

Before configuring subnet routing, make sure `ue1` can reach the camera.

## 6.1 Check the route

On `ue1`:

``` bash
ip route get 192.168.128.10
```

Expected:

``` text
192.168.128.10 dev eno1 src 192.168.128.127 uid 1000
     cache
```

------------------------------------------------------------------------

## 6.2 Test ICMP

On `ue1`:

``` bash
ping -c 4 192.168.128.10
```

A camera may not respond to ping even when RTSP works, so a failed ping
does not necessarily mean the camera is unreachable.

------------------------------------------------------------------------

## 6.3 Test RTSP port

On `ue1`:

``` bash
nc -vz -w 3 192.168.128.10 554
```

Expected:

``` text
Connection to 192.168.128.10 port 554 [tcp/rtsp] succeeded!
```

------------------------------------------------------------------------

## 6.4 Test the actual RTSP stream

The exact RTSP URL used by the camera is project-specific and contains
authentication/stream-path information.

Test it with:

``` bash
ffplay -rtsp_transport tcp "YOUR_EXISTING_RTSP_URL"
```

The RTSP stream was confirmed to work successfully from `ue1`.

This is an important prerequisite: **do not configure Tailscale routing
until the camera's RTSP stream works locally from `ue1`.**

------------------------------------------------------------------------

# 7. Enable IP Forwarding on `ue1`

`ue1` needs to forward traffic between the Tailscale interface and the
camera network.

Run on `ue1`:

``` bash
sudo sysctl -w net.ipv4.ip_forward=1
```

Verify:

``` bash
cat /proc/sys/net/ipv4/ip_forward
```

Expected:

``` text
1
```

------------------------------------------------------------------------

## 7.1 Make IP forwarding persistent

Without this, a reboot could disable forwarding.

Run:

``` bash
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-tailscale.conf
```

Then:

``` bash
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
```

Verify:

``` bash
cat /proc/sys/net/ipv4/ip_forward
```

Expected:

``` text
1
```

------------------------------------------------------------------------

# 8. Advertise the Camera Network Through Tailscale

This is the key Tailscale configuration.

The camera belongs to:

``` text
192.168.128.0/24
```

Therefore, on `ue1` run:

``` bash
sudo tailscale set --advertise-routes=192.168.128.0/24
```

This tells Tailscale:

> `ue1` can route traffic to the `192.168.128.0/24` network.

Do **not** advertise:

``` text
0.0.0.0/0
```

A full Internet route is unnecessary for SemanticEdge.

We only need access to the camera network.

------------------------------------------------------------------------

# 9. Approve the Subnet Route in Tailscale

After running:

``` bash
sudo tailscale set --advertise-routes=192.168.128.0/24
```

open the Tailscale admin console.

Go to:

``` text
Machines
    ↓
ue1
    ↓
Edit route settings
```

Enable/approve:

``` text
192.168.128.0/24
```

Save the configuration.

The route must be approved before other Tailscale machines can use `ue1`
as the subnet router.

------------------------------------------------------------------------

# 10. Verify Tailscale on `ue1`

Run:

``` bash
tailscale status
```

The relevant machine should still appear as:

``` text
ue1
100.124.178.101
```

You can also inspect Tailscale preferences:

``` bash
tailscale debug prefs
```

------------------------------------------------------------------------

# 11. Verify Tailscale on the Mac

On the SemanticEdge MacBook:

``` bash
tailscale status
```

The tailnet should contain both machines:

``` text
100.124.178.101    ue1
100.118.232.36     viveks-macbook-air
```

The Mac can now use the subnet route advertised by `ue1`.

------------------------------------------------------------------------

# 12. Test Remote Access to the Camera

Once the subnet route is approved, test from the Mac.

## 12.1 Ping test

``` bash
ping 192.168.128.10
```

If the camera responds, this confirms IP-level connectivity.

If it does not respond, continue with the RTSP port test because many
CCTV cameras disable ICMP.

------------------------------------------------------------------------

## 12.2 Test RTSP port from the Mac

``` bash
nc -vz -w 5 192.168.128.10 554
```

Expected:

``` text
Connection to 192.168.128.10 port 554 [tcp/rtsp] succeeded!
```

This is more important than ping because SemanticEdge needs TCP/RTSP
connectivity.

------------------------------------------------------------------------

# 13. Test the Actual RTSP Stream From the Remote Mac

This is the final networking test before integrating SemanticEdge.

Use the same RTSP URL that worked on `ue1`.

Example:

``` bash
ffplay -rtsp_transport tcp "YOUR_EXISTING_RTSP_URL"
```

The URL should continue to reference the camera's original private IP:

``` text
192.168.128.10
```

For example, structurally:

``` text
rtsp://USERNAME:PASSWORD@192.168.128.10:554/STREAM_PATH
```

**Do not commit the real username/password to Git.**

The important point is that the Mac does not need a public IP for the
camera.

The traffic is routed:

``` text
Mac
 ↓
Tailscale
 ↓
ue1
 ↓
192.168.128.0/24
 ↓
192.168.128.10
 ↓
RTSP
```

------------------------------------------------------------------------

# 14. RTSP-over-TCP

For the remote setup, RTSP-over-TCP is preferred.

Use:

``` bash
ffplay -rtsp_transport tcp "YOUR_EXISTING_RTSP_URL"
```

instead of simply:

``` bash
ffplay "YOUR_EXISTING_RTSP_URL"
```

The reason is that the RTSP session and media traffic should travel
reliably through the remote network path.

The final path is:

``` text
Sparsh CCTV
    ↓
5G network
    ↓
ue1
    ↓
Tailscale
    ↓
Internet
    ↓
Tailscale
    ↓
Mac
    ↓
SemanticEdge
```

------------------------------------------------------------------------

# 15. Using the Stream in SemanticEdge

The major advantage of this architecture is that **SemanticEdge does not
need to know that the camera is remote**.

The RTSP URL remains based on the camera's original address:

``` text
rtsp://192.168.128.10:554/...
```

For example, if SemanticEdge has:

``` python
RTSP_URL = "rtsp://192.168.128.10:554/..."
```

the same URL can be used from the remote Mac once the Tailscale subnet
route is active.

The network layer handles the remote routing.

------------------------------------------------------------------------

# 16. Final SemanticEdge Data Flow

``` text
                    UNIVERSITY

              Signaltron 5G Network
                       |
                       v
              +----------------+
              |  Sparsh CCTV   |
              | 192.168.128.10 |
              +-------+--------+
                      |
                      | RTSP
                      v
              +----------------+
              |      ue1       |
              |192.168.128.127 |
              |                |
              | Tailscale      |
              |Subnet Router   |
              +-------+--------+
                      |
                      | Encrypted Tailscale
                      |
======================|========================
                      |
                   INTERNET
                      |
======================|========================
                      |
                      v
              +----------------+
              |  SemanticEdge  |
              |     MacBook    |
              |100.118.232.36  |
              +-------+--------+
                      |
                      | RTSP
                      v
              +----------------+
              |     OpenCV     |
              +-------+--------+
                      |
                      v
              +----------------+
              |      YOLO      |
              +-------+--------+
                      |
                      v
              +----------------+
              | Tracking / AI  |
              +-------+--------+
                      |
                      v
                Event Metadata
                      |
                      v
                   MongoDB
```

------------------------------------------------------------------------

# 17. Important: No Public Camera IP Is Required

The final implementation does **not** expose:

``` text
192.168.128.10:554
```

to the public Internet.

The camera remains private.

Only authenticated Tailscale devices in the tailnet can reach the subnet
through `ue1`.

This is considerably safer than directly exposing RTSP port `554` on a
public IP.

------------------------------------------------------------------------

# 18. Why We Chose Tailscale Instead of a Reverse Tunnel

A reverse tunnel was considered as an alternative.

A reverse tunnel would typically look like:

``` text
Camera
   ↓
University machine
   ↓
Reverse tunnel
   ↓
Public VPS
   ↓
Internet
   ↓
Delhi Mac
```

That approach can work, but it introduces another server and another
layer of configuration.

The Tailscale subnet-router solution was preferable for this
SemanticEdge demo because:

-   No VPS is required.
-   No public camera IP is required.
-   No camera configuration change is required.
-   The camera continues using its existing private IP.
-   SemanticEdge continues consuming RTSP directly.
-   The camera does not need to run Tailscale.
-   Tailscale handles the encrypted connection between the remote Mac
    and `ue1`.
-   The solution is relatively easy to troubleshoot.

The final architecture therefore uses:

``` text
Tailscale subnet router
```

rather than:

``` text
Public RTSP server
```

or:

``` text
YouTube/HLS streaming
```

------------------------------------------------------------------------

# 19. Troubleshooting Checklist

## Camera works on `ue1` but not on Mac

Check:

``` bash
tailscale status
```

on both machines.

Then verify that `ue1` is advertising:

``` text
192.168.128.0/24
```

Also verify that the route was approved in the Tailscale admin console.

------------------------------------------------------------------------

## `ping 192.168.128.10` fails

This does not automatically mean the setup is broken.

Test:

``` bash
nc -vz -w 5 192.168.128.10 554
```

If port 554 works, try the RTSP stream directly.

------------------------------------------------------------------------

## RTSP port works but `ffplay` fails

Use TCP transport:

``` bash
ffplay -rtsp_transport tcp "YOUR_EXISTING_RTSP_URL"
```

Also confirm that the exact RTSP URL works on `ue1`.

------------------------------------------------------------------------

## Tailscale machines cannot see each other

Run:

``` bash
tailscale status
```

and confirm both machines are connected:

``` text
ue1
viveks-macbook-air
```

The Tailscale IPs for this setup are:

``` text
ue1:                  100.124.178.101
viveks-macbook-air:   100.118.232.36
```

------------------------------------------------------------------------

## Route exists but traffic does not pass

On `ue1`, verify:

``` bash
cat /proc/sys/net/ipv4/ip_forward
```

It must return:

``` text
1
```

Also verify:

``` bash
ip route get 192.168.128.10
```

Expected:

``` text
192.168.128.10 dev eno1 src 192.168.128.127
```

------------------------------------------------------------------------

# 20. Useful Commands --- Quick Reference

### On `ue1`

Check interfaces:

``` bash
ip addr
```

Check routing table:

``` bash
ip route
```

Find route to camera:

``` bash
ip route get 192.168.128.10
```

Test camera:

``` bash
ping -c 4 192.168.128.10
```

Test RTSP port:

``` bash
nc -vz -w 3 192.168.128.10 554
```

Test RTSP:

``` bash
ffplay -rtsp_transport tcp "YOUR_EXISTING_RTSP_URL"
```

Check IP forwarding:

``` bash
cat /proc/sys/net/ipv4/ip_forward
```

Enable IP forwarding:

``` bash
sudo sysctl -w net.ipv4.ip_forward=1
```

Persist IP forwarding:

``` bash
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-tailscale.conf
```

Apply configuration:

``` bash
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
```

Advertise camera subnet:

``` bash
sudo tailscale set --advertise-routes=192.168.128.0/24
```

Check Tailscale:

``` bash
tailscale status
```

Inspect Tailscale preferences:

``` bash
tailscale debug prefs
```

------------------------------------------------------------------------

### On the SemanticEdge Mac

Check Tailscale:

``` bash
tailscale status
```

Check route:

``` bash
netstat -rn | grep 192.168.128
```

Test camera:

``` bash
ping 192.168.128.10
```

Test RTSP port:

``` bash
nc -vz -w 5 192.168.128.10 554
```

Test RTSP:

``` bash
ffplay -rtsp_transport tcp "YOUR_EXISTING_RTSP_URL"
```

Then use the same RTSP URL in SemanticEdge.

------------------------------------------------------------------------

# 21. Security Notes

Although the CCTV footage itself is acceptable for this project
demonstration, avoid exposing the camera directly to the public
Internet.

Do not configure public port forwarding such as:

``` text
Public_IP:554 → 192.168.128.10:554
```

unless there is a strong operational reason and appropriate security
controls.

Prefer:

``` text
Tailscale
    ↓
Authenticated tailnet
    ↓
Subnet router
    ↓
Private camera
```

Also:

-   Never commit RTSP passwords to Git.
-   Never commit Tailscale authentication keys to Git.
-   Do not share the Tailscale account unnecessarily.
-   Keep `192.168.128.0/24` routing limited to the required tailnet
    devices where practical.
-   For a production deployment, consider advertising only the required
    camera address as a `/32` route if the network design permits it.

------------------------------------------------------------------------

# 22. Production/Demo Checklist

Before leaving for the remote demonstration:

### University side

-   [ ] Sparsh camera powered on
-   [ ] Camera reachable at `192.168.128.10`
-   [ ] `ue1` powered on
-   [ ] `ue1` connected to the university 5G/network
-   [ ] `ue1` has Tailscale connected
-   [ ] IP forwarding enabled
-   [ ] `192.168.128.0/24` route advertised
-   [ ] Route approved in Tailscale admin console
-   [ ] RTSP stream works locally on `ue1`

### Remote Mac

-   [ ] Tailscale installed
-   [ ] Logged into the same tailnet
-   [ ] `ue1` visible in `tailscale status`
-   [ ] Camera reachable at `192.168.128.10`
-   [ ] TCP port 554 reachable
-   [ ] `ffplay -rtsp_transport tcp` works
-   [ ] SemanticEdge receives the RTSP stream
-   [ ] YOLO inference works
-   [ ] Tracking works
-   [ ] MongoDB/event logging works

------------------------------------------------------------------------

# 23. Emergency Fallback

For a live demonstration, do not depend exclusively on a remote network
connection.

Keep a representative CCTV recording locally on the presentation Mac.

If:

``` text
University Internet
      OR
5G network
      OR
ue1
      OR
Tailscale
```

fails during the presentation, SemanticEdge should still be demonstrable
using the recorded footage.

Recommended fallback:

``` text
Recorded CCTV
      ↓
SemanticEdge
      ↓
YOLO
      ↓
Tracking
      ↓
Event generation
      ↓
MongoDB / Dashboard
```

The live remote RTSP setup demonstrates the real-world deployment, while
the recorded stream provides resilience for the presentation.

------------------------------------------------------------------------

# 24. Final Configuration Summary

The completed setup is:

``` text
CAMERA
Sparsh IP CCTV
192.168.128.10:554

        |
        | RTSP
        v

UNIVERSITY ROUTER
ue1
192.168.128.127
interface: eno1
Tailscale: 100.124.178.101

        |
        | Advertised subnet
        | 192.168.128.0/24
        v

TAILSCALE

        |
        | Encrypted connection
        v

REMOTE MAC
viveks-macbook-air
Tailscale: 100.118.232.36

        |
        | RTSP
        v

SEMANTICEDGE
        |
        v
YOLO / Tracking / AI
        |
        v
MongoDB + Dashboard
```

The key configuration command on `ue1` is:

``` bash
sudo tailscale set --advertise-routes=192.168.128.0/24
```

The key network relationship is:

``` text
192.168.128.10
       ↓
192.168.128.127 (ue1)
       ↓
Tailscale
       ↓
100.118.232.36 (Mac)
```

Once the subnet route is approved, the remote Mac can consume the
camera's **original RTSP stream directly**, allowing SemanticEdge to
perform YOLO inference without changing the camera's RTSP architecture.
