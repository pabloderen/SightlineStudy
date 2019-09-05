var express = require('express');

const app = express();
app.use(express.static('public'));
app.use('/model', express.static(__dirname + '/model'));
app.use('/three', express.static(__dirname + '/three'));
app.listen(3000, () =>
  console.log('Example app listening on port 3000!'),
);