document.querySelector('.catalog-button').addEventListener('click', function() {
    document.getElementById('catalog').scrollIntoView({ behavior: 'smooth' });
});

// Пример добавления товара в корзину
document.querySelectorAll('.add-to-cart').forEach(button => {
    button.addEventListener('click', function() {
        this.style.backgroundColor = 'red'; // Изменение цвета кнопки
        // Логика добавления товара в корзину
    });
});
