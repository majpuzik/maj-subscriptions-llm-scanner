const FormData = require('form-data');
const fs = require('fs');

async function quickTest() {
  console.log('🚀 Quick Virtual Try-On Test with optimized images...');
  
  const formData = new FormData();
  formData.append('personImage', fs.createReadStream('/tmp/person-resized.jpg'));
  formData.append('clothingImage', fs.createReadStream('/tmp/clothing-resized.jpg'));
  formData.append('personName', 'Test Model');
  formData.append('clothingName', 'Max Mara Harold Cherry');

  const fetch = (await import('node-fetch')).default;
  
  const response = await fetch('http://localhost:3777/api/try-on', {
    method: 'POST',
    body: formData,
    headers: formData.getHeaders(),
  });

  const data = await response.json();
  console.log('\n✅ Result:', JSON.stringify(data, null, 2));
}

quickTest().catch(console.error);
