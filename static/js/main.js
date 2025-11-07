
let sidebarVisible = window.innerWidth > 768;
let filterFormVisible = false;

async function carregarOpcoesFiltragem() {
    try {
        const response = await fetch('/api/filtros');
        const data = await response.json();

        
        const selectUFs = document.getElementById('filter-ufs');
        if (selectUFs) {
            data.ufs.forEach(uf => {
                const option = document.createElement('option');
                option.value = uf;
                option.textContent = uf;
                selectUFs.appendChild(option);
            });
        }

        const selectTipos = document.getElementById('filter-tipos');
        if (selectTipos) {
            data.tipos_evento.forEach(tipo => {
                const option = document.createElement('option');
                option.value = tipo;
                option.textContent = tipo;
                selectTipos.appendChild(option);
            });
        }

        
        const selectAnos = document.getElementById('filter-anos');
        if (selectAnos) {
            data.anos.forEach(ano => {
                const option = document.createElement('option');
                option.value = ano;
                option.textContent = ano;
                selectAnos.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar opções de filtros:', error);
        mostrarNotificacao('Erro ao carregar filtros', 'danger');
    }
}

function aplicarFiltros(event) {
    event.preventDefault();

    const ufs = Array.from(document.getElementById('filter-ufs').selectedOptions).map(o => o.value);
    const tipos = Array.from(document.getElementById('filter-tipos').selectedOptions).map(o => o.value);
    const anos = Array.from(document.getElementById('filter-anos').selectedOptions).map(o => o.value);

    const params = new URLSearchParams();
    if (ufs.length > 0) params.append('ufs', ufs.join(','));
    if (tipos.length > 0) params.append('tipos_evento', tipos.join(','));
    if (anos.length > 0) params.append('anos', anos.join(','));

    
    const currentPath = window.location.pathname;
    const queryString = params.toString();
    window.location.href = currentPath + (queryString ? '?' + queryString : '');
}

function limparFiltros() {
    document.getElementById('filter-ufs').selectedIndex = 0;
    document.getElementById('filter-tipos').selectedIndex = 0;
    document.getElementById('filter-anos').selectedIndex = 0;
}

function alternarSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');

    if (window.innerWidth <= 768) {
        sidebar.classList.toggle('hidden');
        sidebarVisible = !sidebarVisible;
    }
}

function alternarFiltrosMobile() {
    const sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('show-filters');
    filterFormVisible = !filterFormVisible;
}

async function carregarStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        console.log('Status da API:', data);

        if (data.ultima_atualizacao) {
            const elemento = document.getElementById('ultima-atualizacao');
            if (elemento) {
                elemento.textContent = data.ultima_atualizacao;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar status:', error);
    }
}

function restaurarFiltrosURL() {
    const params = new URLSearchParams(window.location.search);

    const ufs = params.get('ufs');
    if (ufs) {
        const selectUFs = document.getElementById('filter-ufs');
        if (selectUFs) {
            const ufArray = ufs.split(',');
            Array.from(selectUFs.options).forEach(option => {
                option.selected = ufArray.includes(option.value);
            });
        }
    }

    const tipos = params.get('tipos_evento');
    if (tipos) {
        const selectTipos = document.getElementById('filter-tipos');
        if (selectTipos) {
            const tipoArray = tipos.split(',');
            Array.from(selectTipos.options).forEach(option => {
                option.selected = tipoArray.includes(option.value);
            });
        }
    }

    const anos = params.get('anos');
    if (anos) {
        const selectAnos = document.getElementById('filter-anos');
        if (selectAnos) {
            const anoArray = anos.split(',');
            Array.from(selectAnos.options).forEach(option => {
                option.selected = anoArray.includes(option.value);
            });
        }
    }
}

function exportarCSV() {
    const params = new URLSearchParams(window.location.search);
    const queryString = params.toString();
    window.location.href = '/api/exportar-csv' + (queryString ? '?' + queryString : '');
}

function formatarNumero(numero) {
    return numero.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.');
}

function mostrarNotificacao(mensagem, tipo = 'info') {
    const toastHTML = `
        <div class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${tipo} text-white">
                <strong class="me-auto">Notificação</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${mensagem}
            </div>
        </div>
    `;

    const container = document.createElement('div');
    container.className = 'position-fixed bottom-0 end-0 p-3';
    container.style.zIndex = '11';
    container.innerHTML = toastHTML;

    document.body.appendChild(container);

    const toast = new bootstrap.Toast(container.querySelector('.toast'));
    toast.show();

    container.addEventListener('hidden.bs.toast', () => {
        container.remove();
    });
}

function handleWindowResize() {
    if (window.innerWidth > 768) {
        const sidebar = document.getElementById('sidebar');
        if (sidebar) {
            sidebar.classList.remove('hidden');
            sidebarVisible = true;
        }
    }
}

function fecharSidebarAoNavegar() {
    if (window.innerWidth <= 768) {
        const sidebar = document.getElementById('sidebar');
        const navLinks = sidebar.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                sidebar.classList.add('hidden');
                sidebarVisible = false;
            });
        });
    }
}

function otimizarGraficosMobile() {
    if (window.innerWidth <= 768) {
        
        const graficos = document.querySelectorAll('.plotly-graph-div');
        graficos.forEach(grafico => {
            grafico.style.height = '300px';
        });
    }
}

document.addEventListener('DOMContentLoaded', function () {
    
    carregarOpcoesFiltragem();

    restaurarFiltrosURL();

    carregarStatus();

    const filterForm = document.getElementById('filter-form');
    if (filterForm) {
        filterForm.addEventListener('submit', aplicarFiltros);
    }

    const toggleBtn = document.getElementById('toggle-sidebar');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', alternarSidebar);
    }
    
    const btnAtualizarDados = document.getElementById('btn-atualizar-dados');
    if (btnAtualizarDados) {
        btnAtualizarDados.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/atualizar-dados';
        });
    }

    window.addEventListener('resize', handleWindowResize);

    fecharSidebarAoNavegar();

    otimizarGraficosMobile();

    setInterval(carregarStatus, 5 * 60 * 1000);

    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('touchstart', function() {
            this.style.opacity = '0.8';
        });
        btn.addEventListener('touchend', function() {
            this.style.opacity = '1';
        });
    });
});

function copiarParaAreaTransferencia(texto) {
    navigator.clipboard.writeText(texto).then(() => {
        mostrarNotificacao('Copiado para a área de transferência!', 'success');
    }).catch(err => {
        console.error('Erro ao copiar:', err);
        mostrarNotificacao('Erro ao copiar para a área de transferência', 'danger');
    });
}

function abrirEmNovaAba(url) {
    window.open(url, '_blank');
}

function imprimirPagina() {
    window.print();
}

function recarregarPagina() {
    location.reload();
}

function isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

function supportsTouch() {
    return (('ontouchstart' in window) ||
            (navigator.maxTouchPoints > 0) ||
            (navigator.msMaxTouchPoints > 0));
}

if (window.innerWidth <= 768) {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.add('hidden');
        sidebarVisible = false;
    }
}

