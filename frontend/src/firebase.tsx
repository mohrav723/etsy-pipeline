// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getFirestore } from "firebase/firestore";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDDZnzyjXhgtVpUtQwYGZ4F5VXzbjoiTYE",
  authDomain: "etsy-pipeline-4b74a.firebaseapp.com",
  projectId: "etsy-pipeline-4b74a",
  storageBucket: "etsy-pipeline-4b74a.firebasestorage.app",
  messagingSenderId: "675203003477",
  appId: "1:675203003477:web:7161283bf0b35b9aac50dc",
  measurementId: "G-74LLY6N6CD"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

const db = getFirestore(app);

export { db };