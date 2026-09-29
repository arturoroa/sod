/*import AsyncStorage from '@react-native-async-storage/async-storage';

export const setData = async (key: string, value:any) => {
    try{
        await AsyncStorage.setItem(key, value);
        return true;
    }catch (e){
        console.log(`Storing data error: ${e}`);
        return false;
    }
}

export const getData = async (key: string) => {
    try{
        const value = await AsyncStorage.getItem(key);
        return value;
    }catch(e){
        console.log(`Storing data error: ${e}`)
        return null;
    }
}

export const clearData = async (key: string)=> {
    try{
        await AsyncStorage.removeItem(key);
        return true;
    }catch(e){
        console.log(`Storing data error: ${e}`)
        return false;
    }
}

export const getSessionData = async () => {
    const company = await getData('company');
    const UserID = await getData('UserID');
    const type = await getData('usertype');
    const email = await getData('email');
    const phone = await getData('phone');
    const active = await getData('active');

    return {
        "UserID": UserID,
        "Type": type,
        "Company": company,
        "Email": email,
        "Phone": phone,
        "Active": active
    }
}*/

export const setData = (key: string, value:any) => {
    try{
        window.sessionStorage.setItem(key, value);
        return true;
    }catch (e){
        console.log(`Storing data error: ${e}`);
        return false;
    }
}

export const getData = (key: string) => {
    try{
        const value = window.sessionStorage.getItem(key);
        return value;
    }catch(e){
        console.log(`Storing data error: ${e}`)
        return null;
    }
}

export const clearData = (key: string)=> {
    try{
        window.sessionStorage.removeItem(key);
        return true;
    }catch(e){
        console.log(`Storing data error: ${e}`)
        return false;
    }
}

export const getSessionData = () => {
    const company = getData('company');
    const UserID = getData('UserID');
    const type = getData('usertype');
    const email = getData('email');
    const phone = getData('phone');
    const active = getData('active');
    const WebSocketID = getData('WebSocketID');

    return {
        "UserID": UserID,
        "Type": type,
        "Company": company,
        "Email": email,
        "Phone": phone,
        "Active": active,
        "WebSocketID": WebSocketID
    }
}