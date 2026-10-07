// ============ BOTON MOSTRAR CONTRASEÑA ===============================
const togglePassword = document.querySelector('#togglePassword');
const password = document.querySelector('#password');
togglePassword.addEventListener('click', function (e) {
//Quita el metodo predeterminado para el boton mostrar contraseña 
      e.preventDefault();

      const type = password.getAttribute('type') === 'password' ? 'text' : 'password';
      password.setAttribute('type', type);
// Raya al icono del o
    this.classList.toggle('fa-eye');
    this.classList.toggle('fa-eye-slash');
});

// ============ VIBRACION DE LOS IMPUTS ===================================
document.addEventListener('DOMContentLoaded', () => {
  const form = document.querySelector('form');
  const passwordInput = document.querySelector('#password');
  const passwordGroup = passwordInput.closest('.floating-input-group');

  // Función 
  function triggerShake() {
    // Clases de error y animación
    passwordGroup.classList.add('shake', 'error');

    // Quitar animacion luego de 400ms
    setTimeout(() => {
      passwordGroup.classList.remove('shake');
    }, 400);
  }

  // Quitar el borde rojo cuando el usuario vuelva a escribir
  passwordInput.addEventListener('input', () => {
    passwordGroup.classList.remove('error');
  });

//================== VALIDACION =================================

document.querySelector("form").addEventListener("submit", async function(e) {
    e.preventDefault(); // evita que la página se recargue

    const correo = document.getElementById("correo") ? document.getElementById("correo").value : document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
      const respuesta = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ correo: correo, password: password })
      });

      const datos = await respuesta.json();

      if (datos.codigo === 200) {
        alert("Bienvenido " + datos.usuario);
      } else {
        triggerShake(); // Hace temblar el campo cuando la contraseña/usuario es incorrecto
        alert(datos.mensaje);
      }
    } catch (error) {
      triggerShake(); // Hace temblar si falla la conexión con la API
      console.error("Error al conectar con el servidor:", error);
    }
  });

});
