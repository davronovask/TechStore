function initMobileFooter() {
	const footerColumns = document.querySelectorAll(
		'.footer-column:not(.subscribe-section)'
	)

	footerColumns.forEach(column => {
		const header = column.querySelector('h3')

		header.addEventListener('click', () => {
			if (window.innerWidth <= 768) {
				footerColumns.forEach(otherCol => {
					if (otherCol !== column) {
						otherCol.classList.remove('active')
					}
				})

				column.classList.toggle('active')
			}
		})
	})
}