import React, { useEffect, useState } from 'react';
import '../global.css';
import { getData } from './services/storage';
import ListaScreen from './main/mai';
import LoginScreen from './login/login';
import AnalysisComponent from './main/analysis';


const App: React.FC = () =>{
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  const session = (value:boolean) => {
      setIsLoggedIn(value);
  }

  useEffect(()=>{
      const isLoggedIn = async()=>{
          const response = await getData('company');
          if (response != null) {
              setIsLoggedIn(true);
          }else{
              setIsLoggedIn(false);
          }
      }

      isLoggedIn();
  }, []);

  return (
      isLoggedIn?
      <ListaScreen session={session}/>
      :
      <LoginScreen session={session} />
    
  )
}

export default App; 
