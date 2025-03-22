from typing import List, Union, Optional, TYPE_CHECKING
from .BaseTask import BaseTask

if TYPE_CHECKING:
    from .Subtask import Subtask
    from ..LLMs.TaskGenerator import TaskGenerator

class Task(BaseTask):
    """
    작업 관리 시스템의 최상위 작업(Task)을 나타내는 클래스입니다.
    
    Task는 BaseTask를 상속받아 기본 속성(이름, 태그 등)을 포함하며,
    LLM 생성 여부 추적 및 하위 작업(Subtask) 관리 기능을 추가합니다.
    
    Attributes:
        모든 BaseTask 속성을 상속받습니다.
        
        _llm_generated (bool): 이 Task가 LLM에 의해 생성되었는지 추적하는 내부 필드 (기본값: False).
    
    Class Methods:
        create_for_testing: 테스트 목적으로 Task 객체를 생성합니다.
    
    Methods:
        require_llm_generation: 이 Task가 LLM에 의해 생성되었는지 확인합니다.
        set_supertask_of_subtasks: Task를 모든 하위 Subtask의 상위 작업으로 설정합니다.
        add_subtask: 새로운 Subtask를 추가합니다.
        get_all_subtasks: 모든 하위 Subtask의 평면화된 목록을 반환합니다.
        update_total_minutes: 모든 하위 Subtask의 예상 시간을 합산하여 자신의 예상 시간을 업데이트합니다.
        calculate_total_minutes: 자신을 수정하지 않고 모든 하위 Subtask의 총 예상 시간을 계산합니다.
    """
    # LLM 생성 여부를 추적하는 프라이빗 필드
    _llm_generated: bool = False

    # 문자열 기반 타입 어노테이션 사용
    subtasks: List['Subtask'] = []
    
    class Config:
        validate_assignment = True
        extra = "forbid"
        
    def __init__(self, **data):
        super().__init__(**data)
        self._llm_generated = data.get("_llm_generated", False)
    
    def require_llm_generation(self) -> None:
        """
        작업이 LLM에 의해 생성되어야 함을 요구합니다.
        """
        if not self._llm_generated:
            raise ValueError(
                "Task must be generated by LLM."
                "Use TaskGenerator.generate_task() to generate a task."
            )
    
    @classmethod
    def create_for_testing(cls, name: str, **kwargs) -> 'Task':
        """
        테스트 목적으로만 사용하는 메서드입니다.
        실제 사용의 경우 TaskGenerator.generate_task()를 사용하세요.
        """
        return cls(name=name, **kwargs)
    
    def set_supertask_of_subtasks(self) -> None:
        """
        이 작업을 모든 하위 작업의 상위 작업으로 설정하고 하위로 전파합니다.
        """
        for subtask in self.subtasks:
            subtask.set_supertask(self, 'task')
            subtask.set_supertask_of_subtasks()
    
    def add_subtask(self, subtask: 'Subtask') -> None:
        """
        새 하위 작업을 이 작업에 추가합니다.

        Args:
            subtask (Subtask): 추가할 하위 작업.
        """
        super().add_subtask(subtask)
        subtask.set_supertask(self, 'task')
    
    def get_all_subtasks(self) -> List['Subtask']:
        """
        중첩된 하위 작업을 포함한 모든 하위 작업의 평면화된 목록을 가져옵니다.

        Returns:
            List[Subtask]: 모든 레벨의 하위 작업.
        """
        all_subtasks: List['Subtask'] = []
        for subtask in self.subtasks:
            all_subtasks.append(subtask)
            all_subtasks.extend(subtask.get_all_subtasks())
        return all_subtasks
    
    def set_supertask(self) -> None:
        """
        모든 하위 작업의 상위 작업을 설정합니다.
        """
        for subtask in self.subtasks:
            subtask.supertask = self
            subtask.set_supertask()
    
    def __str__(self) -> str:
        """
        작업의 문자열 표현을 반환합니다.
        """
        result = [f"Task: {self.name}"]
        result.append(f"- Context: {self.context}")
        result.append(f"- Location Tags: {self.location_tags}")
        result.append(f"- Time Tags: {self.time_tags}")
        result.append(f"- Other Tags: {self.other_tags}")
        result.append(f"- Estimated Minutes: {self.estimated_minutes}")
        
        if not self.comments == []:
            for i, comment in enumerate(self.comments):
                result.append(f"- Comment {i}: {comment}")
        
        result.append("")
        
        if self.subtasks:
            result.append("Subtasks:")
            for subtask in self.subtasks:
                # 들여쓰기를 적용하여 계층 구조 표현
                subtask_str = str(subtask).replace("\n", "\n  ")
                result.append(f"  {subtask_str}")
        
        return "\n".join(result)
    
    def calculate_total_minutes(self) -> int:
        """
        자신을 수정하지 않고 모든 하위 작업의 총 예상 시간을 계산합니다.

        Returns:
            int: 총 예상 시간(분).
        """
        total_minutes = 0
        for subtask in self.subtasks:
            subtask.update_estimated_minutes()
            total_minutes += subtask.estimated_minutes
        return total_minutes