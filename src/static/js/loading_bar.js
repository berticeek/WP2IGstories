// source: https://codepen.io/splitti/pen/jLZjgx

const svg = document.getElementById('progress_loader')
svg.classList.add('progress-loader')
setInterval(() => {
  svg.classList.toggle('progress-loader')
  svg.classList.toggle('ready-loader')
}, 10000)