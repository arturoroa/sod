import React, { useEffect, useState } from 'react';
import '../global.css';
import { clearData, getData, getSessionData } from './services/storage';
import ListaScreen, { variables } from './main/mai';
import LoginScreen from './login/login';
import { url } from './services/generalService';
import WebSocketsService from './services/WebSocketsServices';
import 'primereact/resources/themes/saga-blue/theme.css';

const App: React.FC = () =>{
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  const session = (value:boolean) => {
      setIsLoggedIn(value);
  }

  const [menuStatus, setMenuStatus] = useState(false)

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

    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
        const sessionData = getSessionData()
        if (sessionData.Company){
            const blob = new Blob([JSON.stringify(sessionData)], { type: "application/json" });
            navigator.sendBeacon(`${url}/logout`, blob)
            WebSocketsService.closeConnection();
            variables.forEach((variable) => {clearData(variable)})
        }
    };
      
  
    window.addEventListener('beforeunload', handleBeforeUnload);
  
    return () => {
        window.removeEventListener('beforeunload', handleBeforeUnload);
    };
      
  }, []);


  return (
            <div className="min-h-screen min-h-[100dvh] w-full overflow-x-hidden bg-[#f4f4f4]">
                {
                    isLoggedIn?
                    <ListaScreen session={session} menuStatus={menuStatus} setMenuStatus={setMenuStatus}/>
                    :
                    <LoginScreen session={session} setMenuStatus={setMenuStatus}/>
                }
            </div>
  )
}

export default App;