const express = require('express');
const app = express();
const os = require('os');
const { exec } = require('child_process');

const port = 3000;

function getIpAddress() {
    const interfaces = os.networkInterfaces();
    let addresses = [];
    for (let iface in interfaces) {
        for (let addr of interfaces[iface]) {
            if (addr.family === 'IPv4' && !addr.internal) {
                addresses.push(addr.address);
            }
        }
    }
    return addresses;
}

function getRunningProcesses() {
    return new Promise((resolve, reject) => {
        exec('ps aux', (error, stdout, stderr) => {
            if (error) {
                reject(stderr);
            } else {
                resolve(stdout);
            }
        });
    });
}

function getDiskSpace() {
    return new Promise((resolve, reject) => {
        exec('df -h /', (error, stdout, stderr) => {
            if (error) {
                reject(stderr);
            } else {
                resolve(stdout);
            }
        });
    });
}

function getTimeSinceBoot() {
    const uptimeSeconds = os.uptime();
    return uptimeSeconds;
}

app.get('/info', async (req, res) => {
    try {
        const [processes, diskSpace] = await Promise.all([getRunningProcesses(), getDiskSpace()]);
        const info = {
            'Service2': {
                'ip_address': getIpAddress(),
                'running_processes': processes,
                'disk_space': diskSpace,
                'time_since_boot_seconds': getTimeSinceBoot()
            }
        };
        res.json(info);
    } catch (error) {
        res.status(500).json({ error: error.toString() });
    }
});

app.listen(port, '0.0.0.0', () => {
    console.log(`Service2 listening on port ${port}`);
});
