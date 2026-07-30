let currentGuilds = [];
let currentChannels = [];
let currentRoles = [];
let loadedPanels = [];

document.addEventListener('DOMContentLoaded', async () => {
    await checkStatus();
    await loadGuilds();
    await loadPanels();
    
    if (document.querySelectorAll('.role-item').length === 0) {
        addRoleRow('🎮', '');
        addRoleRow('🎨', '');
    }
    
    updateLivePreview();
    setInterval(checkStatus, 6000);
});

async function checkStatus() {
    try {
        const res = await fetch('/api/status');
        const data = await res.json();
        
        const badge = document.getElementById('botStatusBadge');
        const text = document.getElementById('botStatusText');
        const banner = document.getElementById('tokenWarningBanner');
        
        badge.className = `status-badge ${data.status}`;
        
        if (data.status === 'online') {
            text.innerText = `Online: ${data.bot_user} (${data.ping_ms || 0}ms)`;
            banner.style.display = 'none';
        } else if (data.status === 'token_required') {
            text.innerText = 'Token Required';
            banner.style.display = 'flex';
        } else {
            text.innerText = 'Connecting...';
            banner.style.display = 'none';
        }
    } catch (err) {
        console.error("Status check failed:", err);
    }
}

function toggleTokenModal() {
    const modal = document.getElementById('tokenModal');
    modal.style.display = modal.style.display === 'none' ? 'block' : 'none';
}

async function saveToken() {
    const token = document.getElementById('tokenInput').value.trim();
    if (!token) return alert('Please enter a valid token');
    
    try {
        const res = await fetch('/api/config/token', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token })
        });
        const data = await res.json();
        if (res.ok) {
            alert(data.message);
            toggleTokenModal();
            checkStatus();
            setTimeout(loadGuilds, 2000);
        } else {
            alert(data.detail || 'Error saving token');
        }
    } catch (err) {
        alert('Failed to save token: ' + err.message);
    }
}

async function loadGuilds() {
    const guildSelect = document.getElementById('guildSelect');
    try {
        const res = await fetch('/api/guilds');
        const data = await res.json();
        currentGuilds = data.guilds || [];
        
        guildSelect.innerHTML = '<option value="">-- Select Discord Server --</option>';
        if (currentGuilds.length === 0) {
            guildSelect.innerHTML = '<option value="">No servers available (Bot offline or not in any server)</option>';
            return;
        }

        currentGuilds.forEach(g => {
            const opt = document.createElement('option');
            opt.value = g.id;
            opt.textContent = `${g.name} (${g.member_count} members)`;
            guildSelect.appendChild(opt);
        });

        if (currentGuilds.length > 0) {
            guildSelect.value = currentGuilds[0].id;
            await onGuildChanged();
        }
    } catch (err) {
        console.error("Failed to load guilds:", err);
    }
}

async function onGuildChanged() {
    const guildId = document.getElementById('guildSelect').value;
    const channelSelect = document.getElementById('channelSelect');
    
    if (!guildId) {
        channelSelect.innerHTML = '<option value="">Select channel...</option>';
        currentRoles = [];
        updateAllRoleDropdowns();
        return;
    }

    try {
        const chRes = await fetch(`/api/guilds/${guildId}/channels`);
        const chData = await chRes.json();
        currentChannels = chData.channels || [];
        
        channelSelect.innerHTML = '<option value="">-- Select Target Channel --</option>';
        currentChannels.forEach(c => {
            const opt = document.createElement('option');
            opt.value = c.id;
            opt.textContent = `# ${c.name} (${c.category})`;
            channelSelect.appendChild(opt);
        });

        const roleRes = await fetch(`/api/guilds/${guildId}/roles`);
        const roleData = await roleRes.json();
        currentRoles = roleData.roles || [];
        
        updateAllRoleDropdowns();
    } catch (err) {
        console.error("Failed to load guild data:", err);
    }
}

function updateAllRoleDropdowns() {
    const dropdowns = document.querySelectorAll('.role-select');
    dropdowns.forEach(select => {
        const savedValue = select.value;
        select.innerHTML = '<option value="">-- Select Role --</option>';
        currentRoles.forEach(r => {
            const opt = document.createElement('option');
            opt.value = r.id;
            opt.textContent = r.name;
            opt.style.color = r.color !== '#99AAB5' ? r.color : 'inherit';
            if (!r.assignable) {
                opt.textContent += ' (Bot role hierarchy lower)';
            }
            select.appendChild(opt);
        });
        if (savedValue) select.value = savedValue;
    });
}

function addRoleRow(emoji = '🎮', roleId = '') {
    const container = document.getElementById('rolesListContainer');
    const rowId = 'role_row_' + Date.now() + '_' + Math.random().toString(36).substr(2, 4);
    
    const row = document.createElement('div');
    row.className = 'role-item';
    row.id = rowId;
    
    row.innerHTML = `
        <input type="text" class="emoji-input" value="${emoji}" placeholder="Emoji" oninput="updateLivePreview()" required>
        <select class="role-select" onchange="updateLivePreview()" required>
            <option value="">-- Select Role --</option>
        </select>
        <button type="button" class="btn btn-danger btn-icon" onclick="removeRoleRow('${rowId}')">✕</button>
    `;
    
    container.appendChild(row);
    updateAllRoleDropdowns();
    if (roleId) {
        const select = row.querySelector('.role-select');
        select.value = roleId;
    }
    updateLivePreview();
}

function removeRoleRow(rowId) {
    const row = document.getElementById(rowId);
    if (row) {
        row.remove();
        updateLivePreview();
    }
}

function insertQuickEmoji(emojiStr) {
    const rows = document.querySelectorAll('.role-item');
    if (rows.length > 0) {
        const lastRowEmojiInput = rows[rows.length - 1].querySelector('.emoji-input');
        if (lastRowEmojiInput && !lastRowEmojiInput.value.trim()) {
            lastRowEmojiInput.value = emojiStr;
            updateLivePreview();
            return;
        }
    }
    addRoleRow(emojiStr, '');
}

function syncColorHex(val) {
    document.getElementById('panelColorHex').value = val.toUpperCase();
}
function syncColorPicker(val) {
    if (/^#[0-9A-F]{6}$/i.test(val)) {
        document.getElementById('panelColor').value = val;
    }
}

function updateLivePreview() {
    const title = document.getElementById('panelTitle').value || 'Reaction Roles';
    const description = document.getElementById('panelDescription').value || '';
    const colorHex = document.getElementById('panelColorHex').value || '#5865F2';
    const thumbnailUrl = document.getElementById('thumbnailUrl').value.trim();
    const imageUrl = document.getElementById('imageUrl').value.trim();
    const footerText = document.getElementById('footerText').value.trim();

    const embedBox = document.getElementById('previewEmbedBox');
    const titleEl = document.getElementById('previewTitle');
    const descEl = document.getElementById('previewDescription');
    const thumbEl = document.getElementById('previewThumbnail');
    const imgEl = document.getElementById('previewImage');
    const footerEl = document.getElementById('previewFooter');
    const reactionsBar = document.getElementById('previewReactionsBar');

    embedBox.style.borderLeftColor = colorHex;
    titleEl.textContent = title;
    descEl.textContent = description;

    if (thumbnailUrl) {
        thumbEl.src = thumbnailUrl;
        thumbEl.style.display = 'block';
    } else {
        thumbEl.style.display = 'none';
    }

    if (imageUrl) {
        imgEl.src = imageUrl;
        imgEl.style.display = 'block';
    } else {
        imgEl.style.display = 'none';
    }

    if (footerText) {
        footerEl.textContent = footerText;
        footerEl.style.display = 'block';
    } else {
        footerEl.style.display = 'none';
    }

    reactionsBar.innerHTML = '';
    const roleRows = document.querySelectorAll('.role-item');
    roleRows.forEach(row => {
        const emoji = row.querySelector('.emoji-input').value.trim();
        const roleSelect = row.querySelector('.role-select');
        const selectedRoleText = roleSelect.options[roleSelect.selectedIndex]?.text || 'Role';
        
        if (emoji) {
            const pill = document.createElement('div');
            pill.className = 'discord-reaction-pill';
            pill.innerHTML = `<span>${emoji}</span> <span style="font-size: 0.75rem; opacity: 0.8;">${selectedRoleText !== '-- Select Role --' ? selectedRoleText : 'Role'}</span>`;
            reactionsBar.appendChild(pill);
        }
    });
}

async function handleFormSubmit(e) {
    e.preventDefault();
    
    const editingId = document.getElementById('editingPanelId').value;
    const guildId = document.getElementById('guildSelect').value;
    const channelId = document.getElementById('channelSelect').value;
    const title = document.getElementById('panelTitle').value.trim();
    const description = document.getElementById('panelDescription').value.trim();
    const color = document.getElementById('panelColorHex').value.trim();
    const thumbnailUrl = document.getElementById('thumbnailUrl').value.trim();
    const imageUrl = document.getElementById('imageUrl').value.trim();
    const footerText = document.getElementById('footerText').value.trim();

    if (!guildId || !channelId) {
        return alert('Please select both a Server and Target Channel');
    }

    const roles = [];
    const roleRows = document.querySelectorAll('.role-item');
    roleRows.forEach(row => {
        const emoji = row.querySelector('.emoji-input').value.trim();
        const roleSelect = row.querySelector('.role-select');
        const roleId = roleSelect.value;
        const roleName = roleSelect.options[roleSelect.selectedIndex]?.text || 'Unknown Role';

        if (emoji && roleId) {
            roles.push({ emoji, role_id: roleId, role_name: roleName });
        }
    });

    if (roles.length === 0) {
        return alert('Please add at least one valid Emoji -> Role mapping!');
    }

    const payload = {
        guild_id: guildId,
        channel_id: channelId,
        title,
        description,
        color,
        thumbnail_url: thumbnailUrl,
        image_url: imageUrl,
        footer_text: footerText,
        roles,
        deploy_immediately: true,
        re_deploy: true
    };

    const submitBtnText = document.getElementById('submitBtnText');
    submitBtnText.textContent = editingId ? 'Updating...' : 'Deploying to Discord...';

    try {
        const url = editingId ? `/api/panels/${editingId}` : '/api/panels';
        const method = editingId ? 'PUT' : 'POST';

        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const data = await res.json();
        if (res.ok) {
            alert(editingId ? 'Panel updated successfully!' : 'Panel created and deployed to Discord!');
            resetForm();
            await loadPanels();
        } else {
            alert('Error: ' + (data.detail || JSON.stringify(data)));
        }
    } catch (err) {
        alert('Failed to save panel: ' + err.message);
    } finally {
        submitBtnText.textContent = editingId ? 'Update & Sync Panel' : 'Deploy Panel to Discord';
    }
}

async function loadPanels() {
    const tableBody = document.getElementById('panelsTableBody');
    try {
        const res = await fetch('/api/panels');
        const data = await res.json();
        loadedPanels = data.panels || [];

        if (loadedPanels.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">
                        No reaction role panels created yet. Create your first panel above!
                    </td>
                </tr>
            `;
            return;
        }

        tableBody.innerHTML = '';
        loadedPanels.forEach(p => {
            const tr = document.createElement('tr');
            
            const rolesBadgeList = (p.roles || []).map(r => `${r.emoji} ${r.role_name}`).join(', ');
            const statusBadge = p.message_id 
                ? `<span class="badge badge-success">Deployed</span>`
                : `<span class="badge badge-pending">Draft</span>`;

            tr.innerHTML = `
                <td><strong>#${p.id}</strong></td>
                <td>
                    <div style="font-weight: 600;">${escapeHtml(p.title)}</div>
                    <div style="font-size: 0.75rem; color: var(--text-muted);">${escapeHtml(p.created_at || '')}</div>
                </td>
                <td><code style="font-size: 0.8rem;">${p.channel_id}</code></td>
                <td><code style="font-size: 0.8rem;">${p.message_id || 'Not Posted'}</code></td>
                <td style="max-width: 200px; font-size: 0.85rem;">${escapeHtml(rolesBadgeList)}</td>
                <td>${statusBadge}</td>
                <td>
                    <div style="display: flex; gap: 0.35rem;">
                        <button class="btn btn-secondary btn-icon" onclick="editPanel(${p.id})" title="Edit Panel">✏️</button>
                        <button class="btn btn-primary btn-icon" onclick="reDeployPanel(${p.id})" title="Re-deploy to Discord">🚀</button>
                        <button class="btn btn-danger btn-icon" onclick="deletePanel(${p.id})" title="Delete Panel">🗑️</button>
                    </div>
                </td>
            `;
            tableBody.appendChild(tr);
        });
    } catch (err) {
        console.error("Failed to load panels:", err);
    }
}

async function editPanel(id) {
    const p = loadedPanels.find(x => x.id === id);
    if (!p) return;

    document.getElementById('editingPanelId').value = p.id;
    document.getElementById('formCardHeading').textContent = `Edit Panel #${p.id}`;
    document.getElementById('submitBtnText').textContent = 'Update & Sync Panel';
    document.getElementById('submitBtnIcon').textContent = '🔄';

    document.getElementById('guildSelect').value = p.guild_id;
    await onGuildChanged();
    document.getElementById('channelSelect').value = p.channel_id;

    document.getElementById('panelTitle').value = p.title;
    document.getElementById('panelDescription').value = p.description;
    document.getElementById('panelColorHex').value = p.color;
    document.getElementById('panelColor').value = p.color;
    document.getElementById('thumbnailUrl').value = p.thumbnail_url || '';
    document.getElementById('imageUrl').value = p.image_url || '';
    document.getElementById('footerText').value = p.footer_text || '';

    document.getElementById('rolesListContainer').innerHTML = '';
    if (p.roles && p.roles.length > 0) {
        p.roles.forEach(r => addRoleRow(r.emoji, r.role_id));
    } else {
        addRoleRow('🎮', '');
    }

    updateLivePreview();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function reDeployPanel(id) {
    try {
        const res = await fetch(`/api/panels/${id}/deploy`, { method: 'POST' });
        const data = await res.json();
        if (res.ok) {
            alert('Panel deployed to Discord channel!');
            loadPanels();
        } else {
            alert('Deployment Error: ' + (data.detail || JSON.stringify(data)));
        }
    } catch (err) {
        alert('Failed to deploy: ' + err.message);
    }
}

async function deletePanel(id) {
    if (!confirm(`Are you sure you want to delete Panel #${id}? This will also delete the message on Discord if possible.`)) return;

    try {
        const res = await fetch(`/api/panels/${id}`, { method: 'DELETE' });
        if (res.ok) {
            alert('Panel deleted.');
            loadPanels();
        } else {
            alert('Error deleting panel');
        }
    } catch (err) {
        alert('Failed to delete: ' + err.message);
    }
}

function resetForm() {
    document.getElementById('editingPanelId').value = '';
    document.getElementById('formCardHeading').textContent = 'Create Reaction Panel';
    document.getElementById('submitBtnText').textContent = 'Deploy Panel to Discord';
    document.getElementById('submitBtnIcon').textContent = '🚀';
    
    document.getElementById('panelTitle').value = 'Self Roles | Pick Your Roles';
    document.getElementById('panelDescription').value = 'React below to pick your server roles:\n\n🎮 - Gamer Role\n🎨 - Creator Role\n📢 - Announcements Role';
    document.getElementById('panelColorHex').value = '#5865F2';
    document.getElementById('panelColor').value = '#5865F2';
    document.getElementById('thumbnailUrl').value = '';
    document.getElementById('imageUrl').value = '';
    document.getElementById('footerText').value = '';

    document.getElementById('rolesListContainer').innerHTML = '';
    addRoleRow('🎮', '');
    addRoleRow('🎨', '');
    updateLivePreview();
}

function escapeHtml(str) {
    return (str || '').replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
