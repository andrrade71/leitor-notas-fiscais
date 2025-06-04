// No topo do seu static/js/script.js:
var allInvoiceItems = []; 
const itemsDataEl = document.getElementById('invoiceItemsDataContainer');
if (itemsDataEl) {
    const itemsJsonString = itemsDataEl.getAttribute('data-items');
    if (itemsJsonString) {
        try {
            const parsed = JSON.parse(itemsJsonString);
            if (Array.isArray(parsed)) {
                allInvoiceItems = parsed;
            } else {
                allInvoiceItems = [];
            }
        } catch (e) {
            console.error("Erro ao parsear JSON de itens do atributo data-items:", e, "String recebida:", itemsJsonString);
            allInvoiceItems = [];
        }
    } else {
        allInvoiceItems = [];
    }
} else {
    allInvoiceItems = [];
}

function copyToClipboard(text, buttonElement) {
    if (
        text === null ||
        typeof text === 'undefined' ||
        (typeof text === 'string' && text.trim() === '') ||
        (typeof text === 'string' && text.trim().toLowerCase() === 'n/a')
    ) {
        if (buttonElement) {
            const originalText = buttonElement.innerText;
            buttonElement.innerText = "Nada!";
            buttonElement.disabled = true;
            setTimeout(() => {
                buttonElement.innerText = originalText;
                buttonElement.disabled = false;
            }, 1500);
        }
        return;
    }
    const textToCopy = text.toString().trim();
    navigator.clipboard.writeText(textToCopy).then(function() {
        if (buttonElement) {
            const originalText = buttonElement.innerText;
            buttonElement.innerText = "Copiado!";
            buttonElement.classList.add('copied');
            buttonElement.disabled = true;
            setTimeout(function() {
                buttonElement.innerText = originalText;
                buttonElement.classList.remove('copied');
                buttonElement.disabled = false;
            }, 1500);
        }
    }).catch(function(err) {
        console.error('Erro ao copiar com navigator.clipboard: ', err);
        let originalButtonText = "Copiar";
        if(buttonElement) {
            originalButtonText = buttonElement.innerText;
        }
        fallbackCopyTextToClipboard(textToCopy, buttonElement, originalButtonText); 
    });
}

function fallbackCopyTextToClipboard(text, buttonElement, originalButtonTextForError) {
    var textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.top = "0";
    textArea.style.left = "0";
    textArea.style.position = "fixed";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    let success = false;
    let currentButtonText = "Copiar"; 
    if(buttonElement) {
         currentButtonText = buttonElement.innerText; 
    }
    try {
        success = document.execCommand('copy');
        if (buttonElement) {
            buttonElement.innerText = success ? "Copiado!" : "Falhou!";
            if(success) buttonElement.classList.add('copied');
            buttonElement.disabled = true;
             setTimeout(function() {
                buttonElement.innerText = currentButtonText; 
                if(success) buttonElement.classList.remove('copied');
                buttonElement.disabled = false;
            }, 1500);
        }
    } catch (err) {
        console.error('Fallback: Erro ao copiar', err);
         if (buttonElement) {
             buttonElement.innerText = "Erro!";
             const revertTo = originalButtonTextForError || "Copiar"; 
             setTimeout(() => {buttonElement.innerText = revertTo;}, 1500);
         }
    }
    document.body.removeChild(textArea);
}


function copyDataAttribute(buttonElement) {
    // Corrige: se o atributo não existe ou está vazio, não tenta copiar
    let jsonString = buttonElement.getAttribute('data-copy-text');
    if (!jsonString || jsonString === 'null' || jsonString === 'undefined') {
        copyToClipboard('', buttonElement);
        return;
    }
    // Remove aspas extras se existirem (caso o valor seja string simples serializada)
    if (jsonString.startsWith('"') && jsonString.endsWith('"')) {
        jsonString = jsonString.slice(1, -1);
    }
    try {
        // Se for string JSON válida, parseia
        const rawValue = JSON.parse(jsonString); 
        // Se for string, remove espaços
        if (typeof rawValue === 'string') {
            copyToClipboard(rawValue.trim(), buttonElement);
        } else {
            copyToClipboard(rawValue, buttonElement);
        }
    } catch (e) {
        // Se não for JSON válido, copia o texto puro já limpo
        copyToClipboard(jsonString.trim(), buttonElement); 
    }
}

function copyDataFromElement(buttonElement) {
    const targetId = buttonElement.getAttribute('data-copy-target-id');
    if (targetId) {
        const targetElement = document.getElementById(targetId);
        if (targetElement) {
            copyToClipboard(targetElement.innerText, buttonElement);
        } else {
            console.error("Elemento alvo para cópia não encontrado:", targetId);
            if (buttonElement) buttonElement.innerText = "Erro!";
        }
    }
}

function formatMoney(val) {
    if (val === null || val === undefined || val === '' || isNaN(val)) return 'N/A';
    return 'R$ ' + Number(val).toFixed(2).replace('.', ',');
}

// Função utilitária para formatar quantidade
function formatQuantity(val) {
    if (val === null || val === undefined || val === '' || isNaN(val)) return 'N/A';
    const qtyNumber = parseFloat(val);
    if (Number.isInteger(qtyNumber)) {
        return qtyNumber.toFixed(0).padStart(2, '0');
    } else {
        return qtyNumber.toString();
    }
}

function copyItemDetailsByIndex(itemIndex, buttonElement) {
    if (typeof allInvoiceItems !== 'undefined' && allInvoiceItems && allInvoiceItems[itemIndex]) {
        const item = allInvoiceItems[itemIndex];
        const quantidade = formatQuantity(item.quantidade);
        const descricao = item.descricao ?? 'N/A';
        const valor = formatMoney(item.valor_total_item);
        const details = `${quantidade} ${descricao} (${valor})`;
        copyToClipboard(details, buttonElement);
    } else {
        console.error("Dados do item não encontrados para o índice:", itemIndex, "em allInvoiceItems:", allInvoiceItems);
        if (buttonElement) {
            const originalText = buttonElement.innerText;
            buttonElement.innerText = "Erro!";
            setTimeout(() => { buttonElement.innerText = originalText; }, 1500);
        }
    }
}

window.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.copy-btn').forEach(btn => {
        if (!btn.hasAttribute('aria-label')) {
            btn.setAttribute('aria-label', 'Copiar valor para a área de transferência');
        }
    });
});