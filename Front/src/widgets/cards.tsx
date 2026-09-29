import { useEffect, useState } from "react";
import { getSessionData } from "../services/storage";
import { httpRequest } from "../services/generalService";
import { Modal } from "./modal";

export const Cards: React.FC<{ endpoint: string, type: string, session:(value:boolean)=>void }> = ({ endpoint, type, session }) => {
    const cardProps:any = {}

    const [card, setCard] = useState(cardProps)
    const [visible, setVisible] = useState(false)
    const [filter, setFilter] = useState(null)

    useEffect(()=>{
        const getData = async () => {
            const sessionData = getSessionData();
            if (sessionData && sessionData.Company){
                const data = await httpRequest('POST', endpoint, sessionData);
                if (data.detail){
                    setCard({title: data.detail})
                }else{
                    setCard(data)
                }
            }else{
                session(false)
            }
        }
        getData();
    }, []);

    const selectedCard = (option:any=null) => {
        setFilter(option)
        setVisible(true)
    }

    return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg m-4 p-6 flex flex-col items-center justify-center min-w-fit flex-1 h-[220px] overflow-hidden">
            <p className="text-center text-[#3b4265] text-base font-bold">
                {card.title}
            </p>
            <div className="my-4 h-px bg-gray-200 w-full" />
            {
                type.toLowerCase()=='percentage'
                ?
                    <>
                        <button className="cursor-pointer" onClick={()=> {selectedCard()}}>
                            <span className="text-center text-3xl">
                                {card.line1??''}
                            </span>
                        </button>
                        <span className="text-center text-sm">
                            {card.line2??''}
                        </span>
                    </>
                :
                    <div className="flex flex-row items-center flex-wrap gap-8 justify-center">
                        {Object.entries(card).slice(1).map(([clave], index) => (
                           <button key={index} className="cursor-pointer" onClick={()=> {selectedCard(`${index}`)}}>
                                <span className="text-center text-base">
                                    {card[clave]}
                                </span>
                            </button> 
                        ))}
                    </div>
            }
            <Modal endpoint={`${endpoint}_filter`} title={card.title} filter={filter} visible={visible} setVisible={setVisible} session={session}/>
        </div>
    );
};