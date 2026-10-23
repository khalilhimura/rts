// SPDX-License-Identifier: GPL-3.0-or-later
document.querySelector('#restart').addEventListener('click',()=>location.reload());
import('./main.js').catch(error => {
    window.frontierGame={status:'failed',error:String(error),history:[]};
    document.querySelector('#status').textContent=String(error);console.error(error);
});
