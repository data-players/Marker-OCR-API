import { render, screen } from '@testing-library/react'
import App from 'App'  // Resolved via modulePaths in jest.config.js

test('renders main application', () => {
  render(<App />)
  const appElement = screen.getByTestId('app')
  expect(appElement).toBeInTheDocument()
}) 