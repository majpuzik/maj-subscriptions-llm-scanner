const FormData = require('form-data');
const fs = require('fs');

async function directTest() {
  console.log('🚀 DIRECT Test - Optimized images');
  console.log('📦 Person: /tmp/person-resized.jpg');
  console.log('📦 Clothing: /tmp/clothing-resized.jpg\n');
  
  const formData = new FormData();
  formData.append('personImage', fs.createReadStream('/tmp/person-resized.jpg'));
  formData.append('clothingImage', fs.createReadStream('/tmp/clothing-resized.jpg'));
  formData.append('personName', 'Test User');
  formData.append('clothingName', 'Max Mara Harold');
  formData.append('clothingCategory', 'upper_body');

  console.log('⏳ Uploading...\n');

  const fetch = (await import('node-fetch')).default;
  
  try {
    const response = await fetch('http://localhost:3777/api/try-on', {
      method: 'POST',
      body: formData,
      headers: formData.getHeaders(),
    });

    console.log('📨 Response status:', response.status);
    const data = await response.json();
    console.log('✅ Response data:', JSON.stringify(data, null, 2));
    
    if (data.success) {
      console.log('\n🎉 SUCCESS! Result URL:', data.resultUrl);
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

directTest();
