function initStickyHeader() {
    const headerElement = document.querySelector('#MyHeader')
    const mainElement = document.querySelector('.main')
    if (!headerElement) {
        console.error('Элемент #MyHeader не найден!')
        return
    }

    window.addEventListener('scroll', () => {
        if (window.scrollY > 58.4) {
            mainElement.classList.add('header-active')
            headerElement.classList.add('fixed')
        } else {
            mainElement.classList.remove('header-active')
            headerElement.classList.remove('fixed')
        }
    })

    const catalogBtn = document.getElementById('catalog-btn')
    const catalogDropdown = document.getElementById('catalog-dropdown')

    if (catalogBtn && catalogDropdown) {
        catalogBtn.addEventListener('click', e => {
            e.stopPropagation()
            catalogDropdown.classList.toggle('active')

            catalogBtn.classList.toggle('btn-active')
        })

        document.addEventListener('click', e => {
            if (
                !catalogDropdown.contains(e.target) &&
                !catalogBtn.contains(e.target)
            ) {
                catalogDropdown.classList.remove('active')
                catalogBtn.classList.remove('btn-active')
            }
        })

        // window.addEventListener('scroll', () => {
        //     catalogDropdown.classList.remove('active');
        // });
    }
}

function initMobileMenu() {
    const burger = document.getElementById('burger-menu')
    const mobileMenu = document.getElementById('mobile-menu')
    const closeBtn = document.getElementById('close-menu-btn')

    const accordionToggle = document.querySelector('.accordion-toggle')
    const accordionContent = document.querySelector('.accordion-content')

    if (accordionToggle && accordionContent) {
        accordionToggle.addEventListener('click', () => {
            accordionToggle.classList.toggle('active')

            if (accordionContent.style.maxHeight) {
                accordionContent.style.maxHeight = null
            } else {
                accordionContent.style.maxHeight = accordionContent.scrollHeight + 'px'
            }
        })
    }

    function openMenu() {
        mobileMenu.classList.add('active')
        document.body.style.overflow = 'hidden'
    }

    function closeMenu() {
        mobileMenu.classList.remove('active')
        document.body.style.overflow = 'auto'

        // Опционально: Закрывать аккордеон при закрытии меню
        /*
        if (accordionToggle && accordionContent) {
            accordionToggle.classList.remove('active');
            accordionContent.style.maxHeight = null;
        }
        */
    }

    if (burger && mobileMenu) {
        burger.addEventListener('click', openMenu)

        if (closeBtn) {
            closeBtn.addEventListener('click', closeMenu)
        }

        mobileMenu.addEventListener('click', e => {
            if (e.target === mobileMenu) {
                closeMenu()
            }
        })
    }
}

// Переключение темы
document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const mobileThemeToggleBtn = document.getElementById('mobile-theme-toggle');
    const body = document.body;

    // Загрузка темы из localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        body.classList.add('theme-light');
    }

    // Функция переключения
    const toggleTheme = () => {
        if (body.classList.contains('theme-light')) {
            body.classList.remove('theme-light');
            localStorage.setItem('theme', 'dark');
        } else {
            body.classList.add('theme-light');
            localStorage.setItem('theme', 'light');
        }
    };

    // Обработчики кликов
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', toggleTheme);
    }
    if (mobileThemeToggleBtn) {
        mobileThemeToggleBtn.addEventListener('click', toggleTheme);
    }
});

initStickyHeader()
initMobileMenu()