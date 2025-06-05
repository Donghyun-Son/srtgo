let token = localStorage.getItem('token') || '';
const tokenInput = document.getElementById('auth-token');
tokenInput.value = token;
document.getElementById('save-token').onclick = () => {
  token = tokenInput.value.trim();
  localStorage.setItem('token', token);
  showMessage('Token saved');
};
document.getElementById('reset-token').onclick = () => {
  api('/token', {method: 'POST'}).then(res => {
    if (res.token) {
      token = res.token;
      tokenInput.value = token;
      localStorage.setItem('token', token);
      showMessage('New token issued');
    }
  });
};

function api(path, options = {}) {
  options.headers = options.headers || {};
  options.headers['Content-Type'] = 'application/json';
  options.headers['X-Auth-Token'] = token;
  return fetch(path, options).then(r => r.json());
}

function showMessage(msg) {
  const box = document.getElementById('messages');
  box.textContent = msg;
  setTimeout(() => box.textContent = '', 4000);
}

function setActive(view) {
  document.querySelectorAll('#nav .nav-link').forEach(a => {
    a.classList.toggle('active', a.dataset.view === view);
  });
  document.querySelectorAll('.view').forEach(s => {
    s.classList.toggle('d-none', s.id !== view);
  });
}

document.getElementById('nav').addEventListener('click', e => {
  if (e.target.dataset.view) setActive(e.target.dataset.view);
});

// Login
const loginForm = document.getElementById('login-form');
loginForm.addEventListener('submit', e => {
  e.preventDefault();
  const data = {
    id: document.getElementById('login-id').value,
    password: document.getElementById('login-password').value,
    rail_type: document.getElementById('login-rail').value
  };
  api('/login', {method:'POST', body: JSON.stringify(data)}).then(res => {
    if (res.message === 'ok') showMessage('Login saved');
    else showMessage(res.message || 'Error');
  });
});

// Search
const searchForm = document.getElementById('search-form');
searchForm.addEventListener('submit', e => {
  e.preventDefault();
  const params = new URLSearchParams({
    departure: document.getElementById('search-departure').value,
    arrival: document.getElementById('search-arrival').value,
    date: document.getElementById('search-date').value.replaceAll('-',''),
    time: document.getElementById('search-time').value.replace(':','')+'00',
    rail_type: document.getElementById('search-rail').value,
    include_no_seats: document.getElementById('include-no-seats').checked,
    include_waiting_list: document.getElementById('include-waiting').checked
  });
  fetch('/reserve?'+params.toString(), {headers:{'X-Auth-Token':token}})
    .then(r=>r.json()).then(showTrains);
});

function showTrains(list) {
  const ul = document.getElementById('train-list');
  ul.innerHTML = '';
  list.forEach(train => {
    const li = document.createElement('li');
    li.className = 'list-group-item d-flex justify-content-between align-items-center';
    li.textContent = `[${train.train_number}] ${train.dep_time} - ${train.arr_time}`;
    const btn = document.createElement('button');
    btn.className = 'btn btn-sm btn-outline-primary';
    btn.textContent = 'Reserve';
    btn.onclick = () => reserveTrain(train);
    li.appendChild(btn);
    ul.appendChild(li);
  });
}

function reserveTrain(train) {
  if (navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({
      type:'reserve',
      payload:{
        token,
        data:{
          departure: document.getElementById('search-departure').value,
          arrival: document.getElementById('search-arrival').value,
          date: document.getElementById('search-date').value.replaceAll('-',''),
          time: train.dep_time,
          rail_type: document.getElementById('search-rail').value,
          seat_type: document.getElementById('seat-type').value,
          passengers:{
            adult: document.getElementById('adult-count').value,
            child: document.getElementById('child-count').value
          },
          pay: document.getElementById('pay-now').checked
        }
      }
    });
    document.getElementById('cancel-bg').classList.remove('d-none');
    showMessage('Reservation started in background');
  }
}

// Reservations
function loadReservations() {
  const rail = document.getElementById('res-rail').value;
  fetch('/reservations?rail_type='+rail, {headers:{'X-Auth-Token':token}})
    .then(r=>r.json()).then(list=>{
      const ul = document.getElementById('reservations-list');
      ul.innerHTML='';
      list.forEach(r=>{
        const li=document.createElement('li');
        li.className='list-group-item d-flex justify-content-between align-items-center';
        li.textContent = r.reservation_number || JSON.stringify(r);
        const btn=document.createElement('button');
        btn.className='btn btn-sm btn-outline-danger';
        btn.textContent='Cancel';
        btn.onclick=()=>cancelReservation(r.reservation_number);
        li.appendChild(btn);
        ul.appendChild(li);
      });
    });
}

document.getElementById('refresh-reservations').onclick=loadReservations;

document.getElementById('cancel-bg').onclick = () => {
  if (navigator.serviceWorker.controller) {
    navigator.serviceWorker.controller.postMessage({type:'cancel'});
    document.getElementById('cancel-bg').classList.add('d-none');
  }
};

function cancelReservation(pnr){
  const rail = document.getElementById('res-rail').value;
  fetch('/reservations/'+pnr+'?rail_type='+rail,{method:'DELETE',headers:{'X-Auth-Token':token}})
    .then(r=>r.json()).then(res=>{showMessage(res.message);loadReservations();});
}

// Settings forms
function simpleForm(id, path) {
  document.getElementById(id).addEventListener('submit', e => {
    e.preventDefault();
    const data = {};
    new FormData(e.target).forEach((v,k)=>data[k]=v);
    api(path,{method:'POST',body:JSON.stringify(data)}).then(res=>showMessage(res.message));
  });
}

simpleForm('card-form','/settings/card');
simpleForm('telegram-form','/settings/telegram');
simpleForm('station-form','/settings/stations');
simpleForm('option-form','/settings/options');

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('sw.js');
  navigator.serviceWorker.addEventListener('message', e => {
    if (e.data.type === 'reserve-result') {
      document.getElementById('cancel-bg').classList.add('d-none');
      showMessage(e.data.success ? 'Reservation complete' : 'Reservation failed');
    }
  });
}
