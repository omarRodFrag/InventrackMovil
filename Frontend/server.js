const express = require('express');
const path = require('path');
const app = express();

// Servir archivos estáticos desde la carpeta www
app.use(express.static(path.join(__dirname, 'www')));

// Todas las rutas que no sean archivos estáticos, servir index.html (para Angular routing)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'www', 'index.html'));
});

const port = process.env.PORT || 8080;
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});

