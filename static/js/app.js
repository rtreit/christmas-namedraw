const form = document.querySelector('#drawForm');
const sendToggle = document.querySelector('#sendEmails');
const scenarioSelect = document.querySelector('#scenarioSelect');
const statusEl = document.querySelector('[data-status]');
const rosterGrid = document.querySelector('[data-roster-grid]');
const hatWrapper = document.querySelector('.hat-wrapper');
const magicHat = document.querySelector('#magicHat');
const drawerSpotlight = document.querySelector('#drawerSpotlight');
const spotlightName = drawerSpotlight?.querySelector('.spotlight-name');

// State
let allParticipants = [];
let scenarios = [];

// Init
async function init() {
  try {
    const [pRes, sRes] = await Promise.all([
      fetch('/api/participants'),
      fetch('/api/scenarios')
    ]);
    
    allParticipants = (await pRes.json()).participants;
    scenarios = (await sRes.json()).scenarios;
    
    updateRoster();
  } catch (e) {
    console.error('Failed to load data', e);
  }
}

function updateRoster() {
  const scenarioId = scenarioSelect?.value;
  const scenario = scenarios.find(s => s.id === scenarioId);
  
  let list = allParticipants;
  if (scenario && scenario.participants.length > 0) {
    list = allParticipants.filter(p => scenario.participants.includes(p.name));
  }
  
  renderRoster(list);
}

function renderRoster(list) {
  rosterGrid.innerHTML = '';
  list.forEach(p => {
    const card = document.createElement('div');
    card.className = 'participant-card';
    card.dataset.email = p.email;
    card.innerHTML = `
      <div class="avatar-placeholder">☃️</div>
      <div class="card-info">
        <span class="card-name">${p.name}</span>
        <span class="card-status">Waiting...</span>
      </div>
    `;
    rosterGrid.appendChild(card);
  });
}

async function runDraw(event) {
  event.preventDefault();
  const btn = form.querySelector('button');
  btn.disabled = true;
  setStatus('Contacting the North Pole...');

  try {
    const response = await fetch('/api/draw', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        send: sendToggle?.checked ?? true,
        scenario_id: scenarioSelect?.value
      })
    });

    if (!response.ok) throw new Error('Grinch detected in the server.');
    
    const data = await response.json();
    const assignments = data.assignments;

    // Start the show
    await playSequence(assignments);
    
    setStatus('All names drawn! Check your inboxes! 🎄');
    celebrate(50); // Big finish

  } catch (error) {
    console.error(error);
    setStatus('Error: ' + error.message);
    btn.disabled = false;
  }
}

if (scenarioSelect) {
  scenarioSelect.addEventListener('change', updateRoster);
}


async function playSequence(assignments) {
  for (const assignment of assignments) {
    await playTurn(assignment);
  }
}

function playTurn(assignment) {
  return new Promise(resolve => {
    const card = rosterGrid.querySelector(`[data-email="${assignment.drawer_email}"]`) || 
                 findCardByName(assignment.drawer);
    
    if (!card) {
      resolve();
      return;
    }

    // 1. Highlight Drawer
    card.classList.add('active');
    updateCardStatus(card, 'Approaching the hat...');
    setStatus(`${assignment.drawer} is reaching in...`);
    
    if (drawerSpotlight && spotlightName) {
      spotlightName.textContent = assignment.drawer;
      drawerSpotlight.classList.add('active');
    }
    
    // 2. Shake Hat
    setTimeout(() => {
      hatWrapper.classList.add('shaking');
      updateCardStatus(card, 'Drawing...');
    }, 500);

    // 3. Reveal/Send
    setTimeout(() => {
      hatWrapper.classList.remove('shaking');
      card.classList.remove('active');
      card.classList.add('done');
      updateCardStatus(card, 'Email Sent! 📨');
      setStatus(`Secret sent to ${assignment.drawer}!`);
      celebrate(10); // Small burst
      
      if (drawerSpotlight) {
        drawerSpotlight.classList.remove('active');
      }
      
      resolve();
    }, 2000);
  });
}

function findCardByName(name) {
  // Fallback if email matching fails
  return Array.from(rosterGrid.children).find(c => 
    c.querySelector('.card-name').textContent === name
  );
}

function updateCardStatus(card, text) {
  const status = card.querySelector('.card-status');
  if (status) status.textContent = text;
}

function setStatus(msg) {
  if (statusEl) statusEl.textContent = msg;
}

function celebrate(count = 20) {
  const colors = ['#ef4444', '#10b981', '#f59e0b', '#ffffff'];
  for (let i = 0; i < count; i++) {
    const confetti = document.createElement('div');
    confetti.className = 'confetti';
    confetti.style.left = Math.random() * 100 + 'vw';
    confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    confetti.style.animationDuration = (Math.random() * 2 + 2) + 's';
    document.body.appendChild(confetti);
    setTimeout(() => confetti.remove(), 4000);
  }
}

if (form) {
  form.addEventListener('submit', runDraw);
}

init();
