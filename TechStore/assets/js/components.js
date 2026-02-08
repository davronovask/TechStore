async function loadComponent(elementId, path) {
	try {
		const response = await fetch(path)
		const html = await response.text()
		document.querySelector(elementId).innerHTML = html
	} catch (error) {
		console.error('Ошибка загрузки компонента:', error)
	}
}