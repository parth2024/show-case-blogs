/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
      './templates/**/*.{html,js}',
      './static/**/*.{html,js}',
      '../daycare_ambassadeurs/templates/**/*.{html,js}',
      '../blog/templates/**/*.{html,js}',
    ],
    theme: {
      extend: {
        fontFamily: { 
            'radio-canada': ['RadioCanada', 'sans-serif'],
            'sans': ['RadioCanada', 'system-ui', 'sans-serif'],
        }
      },
    },
    plugins: [],
  }