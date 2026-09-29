import { useEffect, useState } from "react";
import { getSessionData } from "../services/storage";
import { httpRequest } from "../services/generalService";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { Modal } from "./modal";

export const SimpleTable: React.FC<{ endpoint: string, session:(value:boolean)=>void }> = ({ endpoint, session }) => {
    const dataProps = {
        title: '',
        columns: [],
        data: []
    }

  const [data, setData] = useState(dataProps)
  const [filter, setFilter] = useState('')
  const [visible, setVisible] = useState(false)

  const setSelectedRow = (data:any) => {
    if (data && data.Company) {
      setFilter(data.Company)
      setVisible(true)
    }
  }

  useEffect(()=>{
    const getData = async () => {
      const sessionData = getSessionData();
      if (sessionData && sessionData.Company){
        const data = await httpRequest('POST', endpoint, sessionData);
        if (data.detail) {
          setData({
            title: data.detail,
            columns: [],
            data: []
          })
        }else{
          setData(data)
        }
      }else{
        session(false)
      }
    }
    getData();
  }, []);

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg m-4 p-6 w-auto max-h-[420px] overflow-auto">
        <p className="text-center text-[#3b4265] text-base font-bold">
            {data.title}
        </p>
        <div className="my-4 h-px bg-gray-200 w-full" />
        <DataTable value={data.data} onRowClick={(e) => setSelectedRow(e.data)}>
            {data.columns.map((value, index)=>(
                <Column
                  key={index}
                  field={value}
                  header={value}
                  className="border border-gray-300 p-0"
                  headerStyle={{ textAlign:"left", color: "black", padding: "0px", backgroundColor: "white" }} 
                >
                </Column>
            ))}
        </DataTable>
        <Modal endpoint={`${endpoint}_filter`} title={data.title} filter={filter} visible={visible} setVisible={setVisible} session={session}/>
    </div>
  );
};