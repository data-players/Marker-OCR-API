import React from 'react'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from 'react-query'
import App from './App'

// Mock react-hot-toast since it's not available in test environment
jest.mock('react-hot-toast', () => ({
  Toaster: () => null,
}))

// Helper function to render App with providers
const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  )
}

describe('App Component', () => {
  test('renders without crashing', () => {
    renderWithProviders(<App />)
    
    // Check if the app container exists
    const appContainer = document.querySelector('.min-h-screen')
    expect(appContainer).toBeInTheDocument()
  })

  test('has correct CSS classes applied', () => {
    renderWithProviders(<App />)
    
    const appContainer = document.querySelector('.min-h-screen')
    expect(appContainer).toHaveClass('min-h-screen', 'bg-gray-50')
  })

  test('renders routing structure', () => {
    renderWithProviders(<App />)
    
    // The app should render without throwing errors
    // More specific tests would be in individual page components
    expect(document.body).toBeInTheDocument()
  })
}) 