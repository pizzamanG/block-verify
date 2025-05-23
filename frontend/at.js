(async ()=>{
  const token=localStorage.AgeToken||(document.cookie.match(/AgeToken=([^;]+)/)||[,''])[1];
  if(!token){location.href='/verify.html';return;}
  const [,p]=token.split('.');const d=JSON.parse(atob(p));
  if(Date.now()/1000>d.exp)return location.href='/verify.html';
  const chall=crypto.getRandomValues(new Uint8Array(32));
  try{
    await navigator.credentials.get({publicKey:{challenge:chall,timeout:15000,
      allowCredentials:[{type:'public-key',id:new TextEncoder().encode(d.device)}]}});
    document.body.style.display='block';
  }catch{location.href='/verify.html';}
})();
