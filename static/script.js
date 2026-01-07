document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
    fetchLogs();

    // Auto-refresh logs every 5 seconds
    setInterval(fetchLogs, 5000);

    // Form Submit
    document.getElementById('config-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        await saveConfig();
    });

    // Run Now Button
    document.getElementById('run-now-btn').addEventListener('click', async () => {
        if (confirm('Are you sure you want to run the automation job now?')) {
            await triggerRunNow();
        }
    });

    // Refresh Logs Button
    document.getElementById('refresh-logs').addEventListener('click', fetchLogs);
});

async function loadConfig() {
    try {
        const res = await fetch('/api/config');
        const config = await res.json();

        // Populate FTP
        if (config.ftp) {
            document.getElementById('ftp_host').value = config.ftp.host || '';
            document.getElementById('ftp_port').value = config.ftp.port || 21;
            document.getElementById('ftp_user').value = config.ftp.user || '';
            document.getElementById('ftp_password').value = config.ftp.password || '';
            document.getElementById('ftp_target_dir').value = config.ftp.target_dir || '';
        }

        // Populate Email
        if (config.email) {
            document.getElementById('email_smtp_server').value = config.email.smtp_server || '';
            document.getElementById('email_smtp_port').value = config.email.smtp_port || 587;
            document.getElementById('email_sender_email').value = config.email.sender_email || '';
            document.getElementById('email_sender_password').value = config.email.sender_password || '';
            document.getElementById('email_recipients').value = (config.email.recipients || []).join(', ');
        }

        // Populate Schedule
        if (config.schedule) {
            document.getElementById('schedule_run_time').value = config.schedule.run_time || '09:00';
        }

    } catch (e) {
        console.error("Error loading config:", e);
        alert("Failed to load configuration.");
    }
}

async function saveConfig() {
    const startBtn = document.querySelector('button[type="submit"]');
    const originalText = startBtn.textContent;
    startBtn.textContent = "Saving...";
    startBtn.disabled = true;

    try {
        const formData = {
            ftp: {
                host: document.getElementById('ftp_host').value,
                port: parseInt(document.getElementById('ftp_port').value),
                user: document.getElementById('ftp_user').value,
                password: document.getElementById('ftp_password').value,
                target_dir: document.getElementById('ftp_target_dir').value
            },
            email: {
                smtp_server: document.getElementById('email_smtp_server').value,
                smtp_port: parseInt(document.getElementById('email_smtp_port').value),
                sender_email: document.getElementById('email_sender_email').value,
                sender_password: document.getElementById('email_sender_password').value,
                recipients: document.getElementById('email_recipients').value.split(',').map(s => s.trim())
            },
            schedule: {
                run_time: document.getElementById('schedule_run_time').value
            }
        };

        const res = await fetch('/api/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (res.ok) {
            alert("Configuration saved successfully!");
        } else {
            alert("Failed to save configuration.");
        }
    } catch (e) {
        console.error("Error saving config:", e);
        alert("Error saving configuration.");
    } finally {
        startBtn.textContent = originalText;
        startBtn.disabled = false;
    }
}

async function triggerRunNow() {
    try {
        const res = await fetch('/api/run_now', { method: 'POST' });
        const data = await res.json();
        alert(data.message);
        fetchLogs(); // Immediate log refresh
    } catch (e) {
        console.error("Error running job:", e);
        alert("Failed to trigger job.");
    }
}

async function fetchLogs() {
    try {
        const res = await fetch('/api/logs');
        const data = await res.json();

        const logViewer = document.getElementById('log-viewer');
        if (data.logs && data.logs.length > 0) {
            logViewer.textContent = data.logs.join('');
            logViewer.scrollTop = logViewer.scrollHeight;
        } else {
            logViewer.textContent = "No logs yet...";
        }
    } catch (e) {
        console.error("Error fetching logs:", e);
    }
}
