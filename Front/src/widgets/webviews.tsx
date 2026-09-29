import { useEffect, useState } from "react";
import { ActivityIndicator, Platform, Text, View} from "react-native";
import WebView from "react-native-webview";
import { httpRequest, url } from "../services/generalService";
import { getData, getSessionData, setData } from "../services/storage";
import React from "react";

export const RenderWebView: React.FC<{ endpoint: string, option:boolean }> = ({ endpoint, option }) => {
    const [loading, setLoading] = useState(true);
    const [text, setText] = useState('');
    const [html, setHtml] = useState('');
    const [dash, setDash] = useState('');

    useEffect(()=>{
        const getContent = async()=>{
            setLoading(true);
            let sessionData = await getSessionData();
            if (sessionData && sessionData.Company) {
                let response = null;
                let flag = 0; 
                if (endpoint.includes('get_user_html') || endpoint.includes('get_permission_html')){
                    let value = '0'
                    if (endpoint.includes('get_user_html')){
                        value = '1'
                    }
                    let hasItChanged = await httpRequest('POST', '/get_creation_date', {"Table_num": value, "Company":sessionData.Company, "UserID":sessionData.UserID})
                    if (await getData(`${endpoint}_time`)==null){
                        await setData(`${endpoint}_time`, hasItChanged)
                    }else{
                        if (hasItChanged != null && hasItChanged != await getData(`${endpoint}_time`)){
                            //console.log(`Changes:\nDate before${await getData(`${endpoint}_time`)}\nNew Date: ${hasItChanged}`)
                            let option = false;
                            if (Platform.OS == 'web'){
                                option = window.confirm('New existing information, do you want to refresh?');
                            }
                            if (option){
                                console.log('NEW DATA')
                                await setData(`${endpoint}_time`, hasItChanged)
                            }else{
                                console.log('DEFAULT')
                                try{
                                    response = JSON.parse(await getData(`${endpoint}_content`)??'')
                                }catch(e){
                                    response = await getData(`${endpoint}_content`)
                                }
                                flag = 1;
                            }
                        }
                    }
                }else{
                    flag = 2
                }
                if (flag != 1){
                    response = await httpRequest('POST', endpoint, sessionData);
                }
                if (response){
                    if (typeof response === 'string'){
                        setHtml(response)
                    }else{
                        if (response.url_complementation){
                            setDash(`${url}${response.url_complementation}`)
                        }else{
                            setText(response.detail??'Loading Error')
                        }
                    }
                }else{
                    setText('Loading Error')
                }
                if (flag == 0){
                    if (response.url_complementation || response.detail){
                        await setData(`${endpoint}_content`, JSON.stringify(response))
                    }else{
                        await setData(`${endpoint}_content`, response)
                    }
                }
            }
            setLoading(false);
        }
        getContent()
    }, []);

    return (
        loading?
        (
            option?
                <View className="flex-1 p-6 space-y-8">
                    <ActivityIndicator size="large" />
                </View>
            :
            <ActivityIndicator size="large" />
        )
        :text!=''?
        <Text className="text-center text-gray-500">{text}</Text>
        :Platform.OS=='web'?(
            dash!=''?
            <iframe src={dash}  allowFullScreen style={{height: '100%'}}/>
            :
            <iframe srcDoc={html} allowFullScreen style={{height: '100%'}}/>
        )
        :
        <WebView
            source={{ html: html }}
        />
    );
  };