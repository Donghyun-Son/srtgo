let token = localStorage.getItem('token') || '';

document.getElementById('auth-token').value = token;
document.getElementById('save-token').onclick = () => {
  token = document.getElementById('auth-token').value.trim();
  localStorage.setItem('token', token);
  showMessage('Token saved');
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
  document.querySelectorAll('nav button').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === view);
  });
  document.querySelectorAll('main .view').forEach(s => {
    s.classList.toggle('hidden', s.id !== view);
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
    li.textContent = `[${train.train_number}] ${train.dep_time} - ${train.arr_time}`;
    const btn = document.createElement('button');
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
          rail_type: document.getElementById('search-rail').value
        }
      }
    });
    showMessage('Reservation started in background');
  }
}

// Reservations
function loadReservations() {
  fetch('/reservations?rail_type=SRT', {headers:{'X-Auth-Token':token}})
    .then(r=>r.json()).then(list=>{
      const ul = document.getElementById('reservations-list');
      ul.innerHTML='';
      list.forEach(r=>{
        const li=document.createElement('li');
        li.textContent = r.reservation_number || JSON.stringify(r);
        const btn=document.createElement('button');
        btn.textContent='Cancel';
        btn.onclick=()=>cancelReservation(r.reservation_number);
        li.appendChild(btn);
        ul.appendChild(li);
      });
    });
}

document.getElementById('refresh-reservations').onclick=loadReservations;

function cancelReservation(pnr){
  fetch('/reservations/'+pnr+'?rail_type=SRT',{method:'DELETE',headers:{'X-Auth-Token':token}})
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
      showMessage(e.data.success ? 'Reservation complete' : 'Reservation failed');
    }
  });
}
