const FormData = require('form-data');
const fs = require('fs');

async function finalTest() {
  console.log('\n🎬 ===== FINÁLNÍ TEST VIRTUÁLNÍ ZKUŠEBNÍ KABINY =====\n');
  console.log('👤 Osoba: /tmp/person-resized.jpg (252KB)');
  console.log('👗 Oblečení: /tmp/clothing-resized.jpg (34KB - Max Mara Harold Cherry)\n');
  
  const formData = new FormData();
  formData.append('personImage', fs.createReadStream('/tmp/person-resized.jpg'));
  formData.append('clothingImage', fs.createReadStream('/tmp/clothing-resized.jpg'));
  formData.append('personName', 'Testovací Model');
  formData.append('clothingName', 'Max Mara Harold Cherry');
  formData.append('clothingCategory', 'upper_body');

  console.log('⏳ Odesílám na API...\n');

  const fetch = (await import('node-fetch')).default;
  
  try {
    const response = await fetch('http://localhost:3777/api/try-on', {
      method: 'POST',
      body: formData,
      headers: formData.getHeaders(),
    });

    console.log(`📨 HTTP Status: ${response.status}\n`);
    
    const data = await response.json();
    
    if (data.success) {
      console.log('✅ ===== ÚSPĚCH! =====');
      console.log('🎉 Try-On ID:', data.tryOnId);
      console.log('🖼️  Result URL:', data.resultUrl);
      console.log('\n📸 Otevři v prohlížeči: http://localhost:3777');
      console.log('📚 Historie: http://localhost:3777/api/history\n');
    } else {
      console.log('❌ Chyba:', data.error);
      console.log('📋 Celá odpověď:', JSON.stringify(data, null, 2));
    }
  } catch (error) {
    console.error('\n💥 Fatální chyba:', error.message);
    if (error.stack) console.error('Stack:', error.stack);
  }
}

finalTest();
