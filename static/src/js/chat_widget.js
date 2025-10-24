odoo.define('diet_fitness.chat_widget', function (require) {
    "use strict";
    var publicWidget = require('web.public.widget');

    publicWidget.registry.ChatWidget = publicWidget.Widget.extend({
        selector: 'body',
        start: function () {
            var self = this;
            const chatBox = document.createElement('div');
            chatBox.id = 'cg-widget';
            chatBox.innerHTML = `
              <input id="cg-input" placeholder="Sorunu yaz kanka..."/>
              <button id="cg-send">Gönder</button>
              <div id="cg-output"></div>
            `;
            document.body.appendChild(chatBox);

            document.getElementById('cg-send').onclick = function(){
                const msg = document.getElementById('cg-input').value;
                if(!msg) return;
                fetch('/chatgpt/ask', {
                    method:'POST',
                    headers:{'Content-Type':'application/json'},
                    body:JSON.stringify({message: msg})
                }).then(r=>r.json()).then(data=>{
                    document.getElementById('cg-output').innerText = data.reply;
                });
            }
        }
    });
});
