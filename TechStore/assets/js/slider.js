const slides = document.querySelectorAll('.slide')
const nextBtn = document.querySelector('.next-btn')
const prevBtn = document.querySelector('.prev-btn')

let currentSlideIndex = 0

function showSlide(index) {
	slides.forEach(slide => {
		slide.classList.remove('active')
	})

	slides[index].classList.add('active')
}

function nextSlide() {
	currentSlideIndex = (currentSlideIndex + 1) % slides.length
	showSlide(currentSlideIndex)
}

function prevSlide() {
	currentSlideIndex = (currentSlideIndex - 1 + slides.length) % slides.length
	showSlide(currentSlideIndex)
}

nextBtn.addEventListener('click', nextSlide)
prevBtn.addEventListener('click', prevSlide)

let autoPlayInterval = setInterval(nextSlide, 3000)

const sliderContainer = document.querySelector('.slider-container')

sliderContainer.addEventListener('mouseover', () => {
	clearInterval(autoPlayInterval)
})

sliderContainer.addEventListener('mouseleave', () => {
	autoPlayInterval = setInterval(nextSlide, 3000)
})

showSlide(currentSlideIndex)