const FormData = require('form-data');
const fs = require('fs');
const path = require('path');

async function testVirtualTryOn() {
  const personImagePath = '/Users/m.a.j.puzik/Downloads/20251102_134543.jpg';
  const clothingImagePath = '/Users/m.a.j.puzik/Downloads/1046045206011-a-harold.webp';

  console.log('🎨 Starting Virtual Try-On test...');
  console.log('👤 Person:', personImagePath);
  console.log('👗 Clothing:', clothingImagePath);

  const formData = new FormData();
  formData.append('personImage', fs.createReadStream(personImagePath));
  formData.append('clothingImage', fs.createReadStream(clothingImagePath));
  formData.append('personName', 'Test Person');
  formData.append('clothingName', 'Max Mara Harold Cherry');
  formData.append('clothingCategory', 'upper_body');

  try {
    const fetch = (await import('node-fetch')).default;
    console.log('\n⏳ Sending request to API...');

    const response = await fetch('http://localhost:3777/api/try-on', {
      method: 'POST',
      body: formData,
      headers: formData.getHeaders(),
    });

    const data = await response.json();

    if (data.success) {
      console.log('\n✅ SUCCESS!');
      console.log('🎉 Result URL:', data.resultUrl);
      console.log('🔗 Try-On ID:', data.tryOnId);
      console.log('\n📸 Open in browser: http://localhost:3777');
    } else {
      console.log('\n❌ ERROR:', data.error);
    }
  } catch (error) {
    console.error('\n💥 Request failed:', error.message);
  }
}

testVirtualTryOn();
