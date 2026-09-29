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




  const handleLogout = async () =>  {
    await httpRequest('GET', `/logout/${company}_${UserID}`);
    // Eliminar datos de autenticación del almacenamiento local
    removeData('company');
    removeData('UserID');
    // Actualizar el estado de autenticación
    setIsLoggedIn(false);
  };


  useEffect(()=>{
      const isLoggedIn = async()=>{
          const response = await getData('company');
          if (response != null) {
              setIsLoggedIn(true);
          }else{
              setIsLoggedIn(false);
          }
        };
        isLoggedIn();

    // Agregar evento beforeunload para hacer logout al cerrar la pestaña
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
        event.preventDefault();
        handleLogout();
    };
      
  
      window.addEventListener('beforeunload', handleBeforeUnload);
  
      // Limpiar el evento al desmontar el componente
      return () => {window.removeEventListener('beforeunload', handleBeforeUnload);

};
      
  }, []);


 


  return (
      isLoggedIn?
      <ListaScreen session={session}/>
      :
      <LoginScreen session={session} />
    
  )
}

export default App; 






/*












import React, { useEffect, useState } from 'react';
import '../global.css';
import { getData } from './services/storage';
import ListaScreen from './main/mai';
import LoginScreen from './login/login';
import AnalysisComponent from './main/analysis';


const App: React.FC = () => {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [appState, setAppState] = useState(AppState.currentState);
  
    const session = (value: boolean) => {
      setIsLoggedIn(value);
    };
  
    const logout = async () => {
      // Llamar al endpoint para eliminar la sesión del backend
      await httpRequest('GET', `/logout/${company}_${UserID}`);
  
      // Limpiar la sesión local
      await setData('company', null);
      await setData('usertype', null);
      await setData('active', null);
      await setData('UserID', null);
  
      // Actualizar el estado de la sesión
      session(false);
    };
  
    useEffect(() => {
      const handleAppStateChange = (nextAppState) => {
        if (appState.match(/active|background/) && nextAppState === 'inactive') {
          logout();
        }
        setAppState(nextAppState);
      };
  
      AppState.addEventListener('change', handleAppStateChange);
  
      return () => {
        AppState.removeEventListener('change', handleAppStateChange);
      };
    }, [appState, logout, session]);
  
    useEffect(() => {
      const isLoggedIn = async () => {
        const response = await getData('company');
        if (response != null) {
          setIsLoggedIn(true);
        } else {
          setIsLoggedIn(false);
        }
      };
  
      isLoggedIn();
    }, []);
  
    return (
      isLoggedIn ?
        <ListaScreen session={session} />
        :
        <LoginScreen session={session} />
    );
  };
  
  export default App;
  */