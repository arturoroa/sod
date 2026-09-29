import { useEffect, useState } from "react";
import { getSessionData } from "../services/storage";
import { Chart } from "primereact/chart";
import { httpRequest } from "../services/generalService";
import { Modal } from "./modal";

export const Charts: React.FC<{ endpoint: string, type: string, session:(value:boolean)=>void }> = ({ endpoint, type, session }) => {
  const chartProps = {
    data: {
      labels: [],
      datasets:[]
    },
    options: {
      plugins: {
        title: {
          text: ''
        }
      }
    }
  }

  const [chart, setChart] = useState(chartProps)
  const [visible, setVisible] = useState(false)
  const [filter, setFilter] = useState('')

  useEffect(()=>{
    const getData = async () => {
      const sessionData = getSessionData();
      if (sessionData && sessionData.Company){
        const data = await httpRequest('POST', endpoint, sessionData);
        if (data.detail){
          setChart(
            {
              data: {
                labels: [],
                datasets:[]
              },
              options: {
                plugins: {
                  title: {
                    text: data.detail
                  }
                }
              }
            }
          )
        }else{
          data['options']['onClick']=(event:any, elements:any) => {
            if (elements.length > 0) {
              setFilter(data.data.labels[elements[0].index])
              setVisible(true);
            }
          }
          data['options']['scales']={
            x: {
              ticks: {
                callback: function (value:any, index:any, ticks:any) {
                  const label = data.data.labels[index];
                  return label.length > 15 ? label.substring(0, 15) + "…" : label;
                }
              }
            }
          }
          setChart(data)
        }
      }else{
        session(false)
      }
    }
    getData();
  }, []);

  return (
    type.toLowerCase()=='bar'
    ?
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg m-4 p-6 max-w-full h-[420px] min-w-[275px] flex-1 overflow-hidden">
      <p className="text-center text-[#3b4265] text-base font-bold">
        {chart.options.plugins.title.text}
      </p>
      <div className="my-4 h-px bg-gray-200 w-full" />
      <div className="h-full">
        <Chart type="bar" data={chart.data} options={chart.options} className="w-full h-full"/>
      </div>
      <Modal endpoint={`${endpoint}_filter`} title={chart.options.plugins.title.text} filter={filter} visible={visible} setVisible={setVisible} session={session}/>
    </div>
    :
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg m-4 p-6 flex items-center justify-center max-w-full h-[420px] min-w-[275px] flex-1 overflow-hidden">
      <p className="text-center text-[#3b4265] text-base font-bold">
        {chart.options.plugins.title.text}
      </p>
      <div className="my-4 h-px bg-gray-200 w-full" />
      <div className="h-full w-full">
        <Chart type="doughnut" data={chart.data} options={chart.options} className="w-full h-full"/>    
      </div>
      <Modal endpoint={`${endpoint}_filter`} title={chart.options.plugins.title.text} filter={filter} visible={visible} setVisible={setVisible} session={session}/>
    </div>
  );
};