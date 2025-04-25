const socket = io();

const phrase1Div = document.getElementById('phrase1');
const phrase2Div = document.getElementById('phrase2');
const phrase1Text = document.getElementById('phrase1-text');
const phrase2Text = document.getElementById('phrase2-text');

let currentPhrase1 = null;
let currentPhrase2 = null;

function requestPair() {
    // Clear old text while waiting
    phrase1Text.textContent = '...'; 
    phrase2Text.textContent = '...';
    socket.emit('request_pair');
}

function showPair(p1, p2) {
    currentPhrase1 = p1;
    currentPhrase2 = p2;
    phrase1Text.textContent = currentPhrase1;
    phrase2Text.textContent = currentPhrase2;
    
    // Remove previous listeners if any (safer)
    phrase1Div.onclick = null; 
    phrase2Div.onclick = null; 

    // Add new listeners to the divs
    phrase1Div.onclick = () => vote(currentPhrase1, currentPhrase2);
    phrase2Div.onclick = () => vote(currentPhrase2, currentPhrase1);
}

function vote(winner, loser) {
    // Identify which div was clicked
    const clickedDiv = (winner === currentPhrase1) ? phrase1Div : phrase2Div;

    // Disable clicking while waiting for next pair
    phrase1Div.onclick = null;
    phrase2Div.onclick = null;

    // Add clicked animation class
    clickedDiv.classList.add('phrase-clicked');
    
    // Optional: Visual feedback (e.g., slightly change background)
    // phrase1Div.style.backgroundColor = '#444';
    // phrase2Div.style.backgroundColor = '#444';

    // Send the vote to the server
    socket.emit('vote', { winner, loser });

    // Remove the animation class after a short delay
    setTimeout(() => {
        clickedDiv.classList.remove('phrase-clicked');
    }, 400); // 400ms delay for the flash
}

socket.on('connect', () => {
    console.log('Connected to server');
    requestPair();
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
    phrase1Text.textContent = 'Disconnected';
    phrase2Text.textContent = 'Disconnected';
});

socket.on('new_pair', data => {
    console.log('Received new pair:', data);
    showPair(data.phrase1, data.phrase2);
});

// Initial request in case connect event fires before script fully loads
// requestPair(); // Might not be needed if connect always fires 