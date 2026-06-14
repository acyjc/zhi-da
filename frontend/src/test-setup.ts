import '@testing-library/jest-dom'

// jsdom polyfills
Element.prototype.scrollIntoView = () => {}
Element.prototype.setPointerCapture = () => {}
Element.prototype.releasePointerCapture = () => {}
