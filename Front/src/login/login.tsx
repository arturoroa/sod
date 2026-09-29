import React, { useState } from 'react';
import { View, Text, TextInput, Alert, ImageBackground, TouchableOpacity, ActivityIndicator, Platform } from 'react-native';
import '../../global.css';
import { getSessionData, setData } from '../services/storage';
import { checkStatus, httpRequest } from '../services/generalService';
import WebSocketsService from '../services/WebSocketsServices';

const LoginScreen: React.FC<{session: (value: boolean) => void, setMenuStatus:(value:boolean) => void}> = ({session, setMenuStatus}) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const login = async () => {
    if (email.trim() === '' || password.trim() === '') {
      Alert.alert('Error', 'Please enter all fields.');
      return;
    }
    setLoading(true);
    let response = await httpRequest('POST', '/login', {'UserID':email.trim(), 'Password':password.trim()});
    if (response?.UserType != -1 && response?.UserType != undefined){
      await setData('usertype', response.UserType);
      await setData('company', response.Company);
      await setData('active', response.Active);
      await setData('UserID', response.UserID);
      await setData('email', response.Email);
      await setData('phone', response.Phone);
      await setData('WebSocketID', `${Date.now()}`);

      const sessionData = getSessionData();
      WebSocketsService.newSocket(`${sessionData.Company}_${sessionData.UserID}_${sessionData.WebSocketID}`, () => {}, () => {});
      session(true);

      /*CHECK STATUS*/
      const next = await checkStatus(sessionData, setMenuStatus);
      if (next){
        //console.log('Executing Analysis....\nRemove this function if you think that is slowed')
        await httpRequest('POST', '/execute_analysis', sessionData)
      }
    //  await setData('usertype', '');
    //  await setData('company', 'SOA');
    //  await setData('active', '');
    //  await setData('UserID', 'a');
    //  await setData('email', '');
    //  await setData('phone', '');
    //  await setData('WebSocketID', `${Date.now()}`);
    
    
    }else{
      if (response?.UserType == -1){
        if (Platform.OS == 'web'){
          window.alert('Incorrect User or Password')
        }
      }
    }
    setLoading(false);
  };
  //console.log("Process ID is: " + process.pid);

  return (
    <ImageBackground
      source={require('../../images/bg/AI.jpeg')} // Fondo de pantalla principal
      className="w-full min-h-screen min-h-[100dvh]"
      style={{ width: '100%', minHeight: '100dvh' }}
      imageStyle={{ resizeMode: 'cover' }}
    >
      <View className="flex min-h-screen min-h-[100dvh] w-full justify-center items-center px-4 py-8 sm:px-6 lg:px-8">
        <ImageBackground
          className="w-full max-w-md rounded-2xl border border-white/40 bg-white/75 p-6 shadow-2xl backdrop-blur-sm sm:p-8"
        >
          <Text className="mb-6 text-center text-2xl font-extrabold text-gray-800 sm:text-3xl">
            LogIn
          </Text>
          <TextInput
            placeholder="UserID"
            value={email}
            onChangeText={setEmail}
            className="mb-4 w-full rounded-xl border border-gray-300 bg-white p-3 text-center text-base sm:text-lg"
          />
          <TextInput
            placeholder="Password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
            className="mb-6 w-full rounded-xl border border-gray-300 bg-white p-3 text-center text-base sm:text-lg"
          />
          <TouchableOpacity
            onPress={async()=>{await login()}}
            className="w-full rounded-xl bg-green-600 p-3 shadow-sm transition-colors duration-200 hover:bg-green-700"
          >
            {
              loading?
                <ActivityIndicator size="small" color="#ffffff"/>
              :
              <Text className="text-center text-base font-medium text-white sm:text-lg">
                Submit
              </Text>
            }
          </TouchableOpacity>
        </ImageBackground>
      </View>
    </ImageBackground>
  );
};

export default LoginScreen;

function checktatus() {
  throw new Error('Function not implemented.');
}
