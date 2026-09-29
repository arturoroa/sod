import * as DocumentPicker from 'expo-document-picker';
import { useState } from 'react';
import { TouchableOpacity, View, Text, ActivityIndicator, Platform } from 'react-native';
import { getData, getSessionData } from '../services/storage';
import { upload } from '../services/generalService';

export const UploadFile: React.FC<{ endpoint: string, refresh: ()=> void, setMenuStatus:(value:boolean)=>void, setAnalysisIsCompleted:(value:boolean)=>void, setIsReportActive:(value: boolean)=>void, session:(value:boolean)=>void }> = ({ endpoint, refresh, setMenuStatus, setAnalysisIsCompleted, setIsReportActive, session }) => {
    const [isLoading, setIsLoading] = useState(false);
    
    const uploadFile = async () =>{
        const sessionData = await getSessionData();
        if (sessionData && sessionData.Company){
            try{
                const document = await DocumentPicker.getDocumentAsync({
                    type: [
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        'text/csv',
                        'application/zip'
                    ],
                });
                if (!document.canceled){
                    setIsLoading(true);
                    const response = await upload(endpoint, document, sessionData);
                    if (response.response == null || response.status == 'OK'){
                        //refresh();
                        setMenuStatus(true)
                        setAnalysisIsCompleted(true)
                        setIsReportActive(false)
                        window.alert('Data loaded successfully.')
                    }else{
                        if (response.status && response.status=='ERROR') {
                            if (Platform.OS == 'web'){
                                window.alert(response.response.detail)
                            }
                        }
                    }
                    setIsLoading(false);     
                }
            }catch(e){
                console.log(e)
            }
        }else{
            session(false)
        }
    }

    return (
        <View className="flex justify-center items-center w-full px-3 py-4">
            <TouchableOpacity
                disabled={isLoading}
                onPress={uploadFile}
                className="w-full max-w-md rounded-2xl bg-blue-600 px-6 py-4 shadow-lg transition duration-200 hover:bg-blue-700 active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed"
            >
                <View className="flex flex-row items-center justify-center gap-3">
                    {isLoading && <ActivityIndicator size="small" color="#ffffff" />}
                    <Text className="text-white text-base font-semibold text-center">
                        {isLoading ? 'Uploading ZIP...' : 'Upload ZIP File'}
                    </Text>
                </View>
            </TouchableOpacity>
        </View>
    )
}