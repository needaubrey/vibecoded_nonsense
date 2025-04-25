const socket = io();

function requestLeaderboard() {
    socket.emit('request_leaderboard');
}

function updateLeaderboard(leaderboard) {
    const tbody = document.getElementById('leaderboard-body');
    tbody.innerHTML = '';
    leaderboard.forEach(([phrase, elo], i) => {
        const row = document.createElement('tr');
        row.innerHTML = `<td>${i+1}</td><td>${phrase}</td><td>${elo}</td>`;
        tbody.appendChild(row);
    });
}

socket.on('connect', () => {
    requestLeaderboard();
});

socket.on('leaderboard_update', data => {
    updateLeaderboard(data.leaderboard);
}); 